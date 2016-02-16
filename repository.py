#! /usr/bin/env python
"""Repository module, containing the Repository class.

This class is responsible for running the fixcache algorithm
for a given git repository, which was cloned form GitHub.
"""
import parsing
import cache
import filemanagement as fm
import git
import logging
import itertools
import os
import sys
import constants
import helper_functions

# TODO:
# 1) introduce line count to the file. increase at each commit, if 0,
#    file deleted
# 2) only call get diff when line introduction is needed, otherwise
#    use stat
# 3) revise parsing, correclty is not working correclty
# 4) make all the pick-top-k functions nlogk using a heap


logger = logging.getLogger('fixcache_logger')


class RepositoryError(Exception):
    """Repository Error."""

    def __init__(self, value):
        """Initalization of the class."""
        self.value = value

    def __str__(self):
        """String representation of the class."""
        return repr(self.value)


class Repository(object):
    """Repository class."""

    def __init__(self, repo_dir, cache_ratio=0.1,
                 distance_to_fetch=0.1, branch='master',
                 pre_fetch_size=0.1):
        """Initalization the Repository variables."""
        try:
            self.file_distances = fm.DistanceSet()
            self.file_set = fm.FileSet()
            self.commit_order = {}
            self.cache_ratio = cache_ratio
            self.hit_count = 0
            self.miss_count = 0
            self.repo_dir = repo_dir

            repo_full_path = os.path.join(constants.REPO_DIR, repo_dir)
            self.repo = git.Repo(repo_full_path)
            assert not self.repo.bare
            self.commit_list = list(reversed(
                list(self.repo.iter_commits(branch))))

            self.file_count = self._get_file_count(self.commit_list[-1])
            self.cache_size = int(self.cache_ratio * float(self.file_count))

            # initializing commit hash to order mapping
            self.cache = cache.SimpleCache(self.cache_size)
            self.distance_to_fetch = self._get_dtf(distance_to_fetch)
            self.pre_fetch_size = self._get_pfs(pre_fetch_size)
            self._init_commit_order()
        except git.exc.NoSuchPathError:
            raise RepositoryError(
                "The path %s is not a valid repository" % (repo_dir))
        except ValueError as ve:
            logging.warning(ve)
            raise RepositoryError(
                "Error occurred during Repository initalization")

    @property
    def cache_ratio(self):
        """Cache ratio controls the persentage of files to be in the cache."""
        return self._cache_ratio

    @cache_ratio.setter
    def cache_ratio(self, value):
        if value < 0.01 or value > 1.0:
            raise ValueError("Cache ratio has to be between 0.01 or 1.00")
        self._cache_ratio = value

    @property
    def distance_to_fetch(self):
        """Distance to fetch, used when fetching files at bug introduction."""
        return self._distance_to_fetch

    @distance_to_fetch.setter
    def distance_to_fetch(self, value):
        if value < 0:
            raise ValueError(
                'distance_to_fetch has to be a non-negative integer')
        self._distance_to_fetch = value

    @property
    def pre_fetch_size(self):
        """Per revision pre fetch size. Fetching new/changed files."""
        return self._pre_fetch_size

    @pre_fetch_size.setter
    def pre_fetch_size(self, value):
        if value < 0:
            raise ValueError(
                'pre-fetch size has to be a non-negative integer')
        self._pre_fetch_size = value

    def reset(self, cache_ratio=None, distance_to_fetch=None, pfs=None):
        """Reset the cache after each analysis."""
        self.hit_count = 0
        self.miss_count = 0
        self.file_distances.reset()
        self.file_set.reset()

        if cache_ratio is not None:
            self.cache_ratio = cache_ratio
            self.file_count = self._get_file_count(self.commit_list[-1])
            self.cache_size = int(self.cache_ratio * float(self.file_count))
            if self.cache_size == 0:
                self.cache_size = 1

        if distance_to_fetch is not None:
            self.distance_to_fetch = self._get_dtf(distance_to_fetch)

        if pfs is not None:
            self.pre_fetch_size = self._get_pfs(pfs)

        self.cache.reset(self.cache_size)

    def run_fixcache(self):
        """Run fixcache with the given variables."""
        for commit in self.commit_list:
            logger.debug('Currently at %s' % commit)
            parents = commit.parents
            if len(parents) == 1:
                # return the list of tuples by file info
                f_info = self.file_set.get_and_update_multiple(
                    git_stat=commit.stats.files,
                    commit_num=self.commit_order[commit.hexsha])
                changed_files = [
                    x[1] for x in filter(lambda x: x[0] == 'changed', f_info)
                ]

                deleted_files = [
                    x[1] for x in filter(lambda x: x[0] == 'deleted', f_info)
                ]

                created_files = [
                    x[1] for x in filter(lambda x: x[0] == 'created', f_info)
                ]

                self._cleanup_files(deleted_files)

                self.file_set.changed_several(
                    changed_files, self.commit_order[commit.hexsha])

                files = [x[1] for x in f_info]

                self._update_distance_set(
                    created_files + changed_files, commit)

                if parsing.is_fix_commit(commit.message):
                    for file_ in changed_files:
                        file_.fault(self.commit_order[commit.hexsha])
                        deleted_line_dict = self._get_diff_deleted_lines(
                            commit, parents[0])
                        # print deleted_line_dict
                        del_lines = deleted_line_dict[file_.path]
                        if self.cache.file_in(file_):
                            self.hit_count += 1
                        else:
                            self.miss_count += 1
                            self.cache.add(file_)

                            line_intr_c = self._get_line_introducing_commits(
                                del_lines, file_.path, commit.parents[0])

                            closest_file_set = []

                            for c in line_intr_c:
                                # get closest files is nlogk, so optimal
                                cf = self.file_distances.get_closest_files(
                                    file_,
                                    self.distance_to_fetch,
                                    self.commit_order[c.hexsha])
                                closest_file_set += cf

                            # there is no need for pre sorting, as already
                            # fetchiing closest files
                            self.cache.add_multiple(
                                closest_file_set, pre_sort=False)

                new_entity_pre_fetch = self._get_per_rev_pre_fetch(
                    created_files, commit)

                changed_entity_pre_fetch = self._get_per_rev_pre_fetch(
                    changed_files, commit)

                self.cache.add_multiple(new_entity_pre_fetch)
                self.cache.add_multiple(changed_entity_pre_fetch)
            elif len(parents) == 0:
                # initial commit
                files = self._get_commit_tree_files(commit)
                files_to_add = []
                for path in files:
                    line_count = self._get_line_count(path, commit)
                    created, file_ = self.file_set.get_or_create_file(
                        file_path=path, line_count=line_count)
                    if not created:
                        file_.line_count = line_count
                    files_to_add.append(file_)
                self.cache.add_multiple(files_to_add)
            else:
                pass

    def _cleanup_files(self, files):
        return
        self.file_set.remove_files(files)
        self.file_distances.remove_files(files=files)
        self.cache.remove_files(files=files)

    def _get_per_rev_pre_fetch(self, file_list, commit):
        if len(file_list) <= self.pre_fetch_size:
            return file_list

        loc_file_list = helper_functions.get_top_elements(
            [(-x.line_count, x) for x in file_list],
            self.pre_fetch_size)

        return [x[1] for x in loc_file_list]

    def _get_dtf(self, dtf):
        if dtf is None:
            distance_to_fetch = 1
            return distance_to_fetch

        if isinstance(dtf, int):
            return dtf
        elif isinstance(dtf, float):
            dtf = int(dtf * float(self.cache_size))
            if dtf == 0:
                return 1
            else:
                return dtf

    def _get_pfs(self, pfs):
        if pfs is None:
            return 1

        if isinstance(pfs, int):
            return pfs
        elif isinstance(pfs, float):
            pfs = int(pfs * float(self.cache_size))
            if pfs == 0:
                return 1
            else:
                return pfs

    def _init_commit_order(self):
        commit_counter = 0
        for commit in self.commit_list:
            self.commit_order[commit.hexsha] = commit_counter
            commit_counter += 1

    def _update_distance_set(self, files, commit):
        file_pairs = list(itertools.combinations(files, 2))

        for pair in file_pairs:
            self.file_distances.add_occurrence(
                *pair, commit=self.commit_order[commit.hexsha])

    def _get_file_count(self, commit):
        return len(self._get_commit_tree_files(commit))

    def _get_line_count(self, file_, commit):
        line_count = 0
        for commit, lines in self.repo.blame(commit, file_):
            line_count += len(lines)

        return line_count

    def _get_line_introducing_commits(self, line_list, file_, commit):
        """Return the set of commits which introduced lines in a file.

        Ideally this will be a single commit, not more.

        :type line_list: int tuple list
        :param line_list: The list of tuples specifying the lines

        :type file: str
        :param file: The string representation of a file in the repo

        :commit line_list: Commit object
        :param line: Commit object. The point in history where we want to
                     look at the file

        :rtype: Commit set
        :return: Returns the set of commits which introduced the line_list
        """
        commit_list = []
        commit_set = []
        try:
            for commit, lines in self.repo.blame(commit, file_):
                commit_list += [(commit, x) for x in lines]
        except git.exc.GitCommandError:
            return set()
        finally:
            pass
        if len(commit_list) == 0:
            return set()

        for line_number in line_list:
            commit, line = commit_list[line_number]
            if parsing.important_line(line):
                commit_set.append(commit)

        return set(commit_set)

    def _get_diff_deleted_lines(self, commit1, commit2):
        """Return a list of blobs which changed from commit1 to commit2.

        :type commit1: Commit object
        :param commit1: The child commit, which is newer

        :type commit2: Commit object
        :param commit2: The parent commit, which is older

        :rtype: tuple of file, deleted lines and change type
        :return: Returns a list of tuples with specification as above
        """
        diffs = commit2.diff(commit1, create_patch=True, unified=True)

        file_dict = {}
        for diff in diffs:
            deleted_lines = parsing.get_deleted_lines_from_diff(
                diff.diff.splitlines())
            if diff.b_path is not None:
                file_dict[diff.a_path] = deleted_lines
            elif diff.a_path is not None:
                file_dict[diff.a_path] = deleted_lines
            else:
                pass

        return file_dict

    def _get_commit_tree_files(self, commit):
        """Retrn a list of blobs for a given commit.

        :type commit: Commit object
        :param commit: The input commit for which we want to know the list of
                        file_list

        :rtype: string list
        :return: List of strings representing the filename
        """
        file_list = []
        for item in commit.tree.traverse():
            if item.type == 'blob':
                # probably not the best way, as O(n^2) for the function
                file_list.append(item.path)

        return file_list

    def _get_number_of_files(self):
        """Return the number of files and head.

        :rtype: int
        :return: the number of files at head
        """
        file_list = self._get_commit_tree_files(self.commit_list[0])

        return len(file_list)


class WindowedRepository(Repository):
    """WindowedRepository class, used for alternativy evaluation."""

    def __init__(self, window=0.9, *args, **kwargs):
        """Initalization of Repository variables, with window variables."""
        super(WindowedRepository, self).__init__(*args, **kwargs)
        self.window = window
        commit_list_len = len(self.commit_list)
        new_len = int(self.window * float(commit_list_len))
        self.horizon_commit_list = self.commit_list[new_len:]
        self.commit_list = self.commit_list[:new_len]
        self.horizon_faulty_file_set = set()
        self.horizon_normal_file_set = set()

    def window_init(self, window=None):
        """Initalization of a new window."""
        pass
        # TODO use a single function for reset and init

    def reset(self, window=None, *args, **kwargs):
        """Reset the WindowedRepository."""
        super(WindowedRepository, self).reset(*args, **kwargs)
        if window is not None:
            self.window = window
            commit_list_len = len(self.commit_list)
            new_len = int(self.window * float(commit_list_len))
            c_list = self.commit_list + self.horizon_commit_list
            del self.horizon_commit_list
            del self.commit_list

            self.commit_list = c_list[:new_len]
            self.horizon_commit_list = c_list[new_len:]

        self.reset_horizon()

    def reset_horizon(self):
        """Reset horizon of WindowedRepository."""
        del self.horizon_faulty_file_set
        self.horizon_faulty_file_set = set()

        del self.horizon_normal_file_set
        self.horizon_normal_file_set = set()


def main():
    """Main entry point for the script."""
    r = WindowedRepository(
        window=0.9, repo_dir=constants.FACEBOOK_SDK_REPO, cache_ratio=0.1)
    print len(r.commit_list)
    r.run_fixcache()
    print r.hit_count
    print r.miss_count

if __name__ == '__main__':
    sys.exit(main())
