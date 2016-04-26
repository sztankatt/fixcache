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


class RepositoryMixin(object):
    """Repository mixin."""

    def __init__(self, repo_dir, cache_ratio=0.1, branch='master'):
        """Init."""
        self.file_set = fm.FileSet()
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
        self.commit_order = {}
        self._init_commit_order()

    def _init_commit_order(self):
        commit_counter = 0
        for commit in self.commit_list:
            logger.debug('Initializing commit %s' % (commit))
            self.commit_order[commit.hexsha] = commit_counter
            commit_counter += 1

    def _get_file_count(self, commit):
        return len(self._get_commit_tree_files(commit))

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

    def _get_line_count(self, file_, commit):
        line_count = 0
        for commit, lines in self.repo.blame(commit, file_):
            line_count += len(lines)

        return line_count


class RandomRepository(RepositoryMixin):
    """Repository implementing random behavior."""

    def __init__(self, *args, **kwargs):
        """Init."""
        super(RandomRepository, self).__init__(*args, **kwargs)
        self.distance_to_fetch = None
        self.pre_fetch_size = None

    def run_fixcache(self):
        """Run fixcache for RandomRepository."""
        for commit in self.commit_list:
            logger.debug('Currently at %s' % commit)
            parents = commit.parents
            if len(parents) == 1:
                # return the list of tuples by file info
                f_info = self.file_set.get_and_update_multiple(
                    git_stat=commit.stats.files,
                    commit_num=self.commit_order[commit.hexsha])
                files = [
                    x[1] for x in filter(
                        lambda x: x[0] == 'changed' or x[0] == 'created',
                        f_info)
                ]

                deleted_files = [
                    x[1] for x in filter(lambda x: x[0] == 'deleted', f_info)
                ]

                self.file_set.remove_files(deleted_files)

                if parsing.is_fix_commit(commit.message):
                    random_file_set = self.file_set.get_random(self.cache_size)
                    for file_ in files:
                        if file_.path in random_file_set:
                            self.hit_count += 1
                        else:
                            self.miss_count += 1

            elif len(parents) == 0:
                # initial commit
                files = self._get_commit_tree_files(commit)
                files_to_add = []
                for path in files:
                    line_count = self._get_line_count(path, commit)
                    created, file_ = self.file_set.get_or_create_file(
                        file_path=path, line_count=line_count)
                    files_to_add.append(file_)
            else:
                pass

    def reset(self, cache_ratio=None, **kwargs):
        """Reset the cache after each analysis."""
        self.hit_count = 0
        self.miss_count = 0
        self.file_set.reset()

        if cache_ratio is not None:
            self.cache_ratio = cache_ratio
            self.file_count = self._get_file_count(self.commit_list[-1])
            self.cache_size = int(self.cache_ratio * float(self.file_count))
            if self.cache_size == 0:
                self.cache_size = 1


class Repository(RepositoryMixin):
    """Repository class."""

    def __init__(self, repo_dir, cache_ratio=0.1,
                 distance_to_fetch=0.1, branch='master',
                 pre_fetch_size=0.1):
        """Initalization the Repository variables."""
        try:
            super(Repository, self).__init__(
                repo_dir, cache_ratio=cache_ratio, branch=branch)
            self.file_distances = fm.DistanceSet()

            # initializing commit hash to order mapping
            self.cache = cache.Cache(self.cache_size)
            self.distance_to_fetch = self._get_distance_to_fetch(
                distance_to_fetch)
            self.pre_fetch_size = self._get_pre_fetch_size(pre_fetch_size)
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

    def reset(self, cache_ratio=None, distance_to_fetch=None,
              pre_fetch_size=None):
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
            self.distance_to_fetch = self._get_distance_to_fetch(
                distance_to_fetch)

        if pre_fetch_size is not None:
            self.pre_fetch_size = self._get_pre_fetch_size(pre_fetch_size)

        self.cache.reset(self.cache_size)

    def run_fixcache(self):
        """Run fixcache with the given variables."""
        for commit in self.commit_list:
            # print '[%s]Currently at %s' % (
            #    datetime.datetime.fromtimestamp(commit.committed_date).year,
            #    commit)
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

                self._update_distance_set(
                    created_files + changed_files, commit)

                if parsing.is_fix_commit(commit.message):
                    for file_ in changed_files:
                        file_.fault(self.commit_order[commit.hexsha])
                        if self.cache.file_in(file_):
                            self.hit_count += 1
                        else:
                            deleted_line_dict = self._get_diff_deleted_lines(
                                commit, parents[0])
                            # print deleted_line_dict
                            del_lines = deleted_line_dict[file_.path]
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

                            closest_file_set = list(set(closest_file_set))
                            # there is no need for pre sorting, as already
                            # fetchiing closest files
                            self.cache.add_multiple(
                                closest_file_set)

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
        self.file_set.remove_files(files)
        self.file_distances.remove_files(files=files)
        self.cache.remove_files(files=files)

    def _get_per_rev_pre_fetch(self, file_list, commit):
        if len(file_list) <= self.pre_fetch_size:
            return file_list

        loc_file_list = helper_functions.get_top_elements(
            [(x.line_count, x) for x in file_list],
            self.pre_fetch_size)

        return [x[1] for x in loc_file_list]

    def _get_distance_to_fetch(self, distance_to_fetch):
        if distance_to_fetch is None:
            distance_to_fetch = 1
            return distance_to_fetch

        if isinstance(distance_to_fetch, int):
            return distance_to_fetch
        elif isinstance(distance_to_fetch, float):
            distance_to_fetch = int(distance_to_fetch * float(self.cache_size))
            if distance_to_fetch == 0:
                return 1
            else:
                return distance_to_fetch

    def _get_pre_fetch_size(self, pre_fetch_size):
        if pre_fetch_size is None:
            return 1

        if isinstance(pre_fetch_size, int):
            return pre_fetch_size
        elif isinstance(pre_fetch_size, float):
            pre_fetch_size = int(pre_fetch_size * float(self.cache_size))
            if pre_fetch_size == 0:
                return 1
            else:
                return pre_fetch_size

    def _update_distance_set(self, files, commit):
        file_pairs = list(itertools.combinations(files, 2))

        for pair in file_pairs:
            self.file_distances.add_occurrence(
                *pair, commit=self.commit_order[commit.hexsha])

    def _get_line_introducing_commits(self, line_list, file_path, commit):
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
            for line_intr_c, lines in self.repo.blame(commit, file_path):
                commit_list += [(line_intr_c, x) for x in lines]

        except git.exc.GitCommandError:
            print "git.exc.GitCommandError"
            return set()
        finally:
            pass
        if len(commit_list) == 0:
            return set()
        for line_num in line_list:
            introducing_commit, line = commit_list[line_num]
            if parsing.important_line(line):
                commit_set.append(introducing_commit)

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
        diffs = commit2.diff(commit1, create_patch=True, unified=0)
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

    def _get_number_of_files(self):
        """Return the number of files and head.

        :rtype: int
        :return: the number of files at head
        """
        file_list = self._get_commit_tree_files(self.commit_list[0])

        return len(file_list)


class WindowedRepository(Repository):
    """WindowedRepository class, used for alternativy evaluation.

    True positive: in cache, and in horizon
    False positive: in the cache, but not in the horizon
    True negative: not in the cache, and not in the horizon
    False negative: not in the cache, but in the horizon.
    """

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
        self.evaluation_data = {
            'true_positive': 0,
            'true_negative': 0,
            'false_positive': 0,
            'false_negative': 0
        }

    def reset(self, window=None, *args, **kwargs):
        """Reset the WindowedRepository."""
        super(WindowedRepository, self).reset(*args, **kwargs)
        if window is not None:
            self.window = window
            c_list = self.commit_list + self.horizon_commit_list

            commit_list_len = len(c_list)
            new_len = int(self.window * float(commit_list_len))

            del self.horizon_commit_list
            del self.commit_list

            self.commit_list = c_list[:new_len]
            self.horizon_commit_list = c_list[new_len:]
        self.evaluation_data = {
            'true_positive': 0,
            'true_negative': 0,
            'false_positive': 0,
            'false_negative': 0
        }

        self.reset_horizon()

    def reset_horizon(self):
        """Reset horizon of WindowedRepository."""
        del self.horizon_faulty_file_set
        self.horizon_faulty_file_set = set()

        del self.horizon_normal_file_set
        self.horizon_normal_file_set = set()

    def evaluate(self):
        """Run fixcache, then calculate TP/TN/FP/FN."""
        self.run_fixcache()
        print self.hit_count
        print self.miss_count

        cache_set = self.cache.file_set

        output = []

        counter = 1

        for commit in self.horizon_commit_list:
            if len(commit.parents) == 1:
                files = self.file_set.get_existing_multiple(commit.stats.files)

                if parsing.is_fix_commit(commit.message):
                    # add files to horizon_faulty."""
                    map(lambda x: self.horizon_faulty_file_set.add(x),
                        files)

                    normal_set = self.horizon_normal_file_set \
                        - self.horizon_faulty_file_set

                    faulty_set = self.horizon_faulty_file_set

                    true_positive = len(cache_set & faulty_set)
                    false_positive = len(cache_set & normal_set)
                    true_negative = len(normal_set - cache_set)
                    false_negative = len(faulty_set - cache_set)
                    file_count = len(normal_set | faulty_set)

                    out = (counter, true_positive, false_positive,
                           true_negative, false_negative,
                           file_count, commit.hexsha)

                    output.append(out)

                else:
                    # add files to horizon normal
                    map(lambda x: self.horizon_normal_file_set.add(x),
                        files)

                counter += 1

        """
        True positive: in cache, and in horizon
        False positive: in the cache, but not in the horizon
        True negative: not in the cache, and not in the horizon
        False negative: not in the cache, but in the horizon.
        """

        return output


def main():
    """Main entry point for the script."""
    logger = logging.getLogger('fixcache_logger')
    logger.setLevel(logging.INFO)
    r = RandomRepository(
        repo_dir=constants.FACEBOOK_SDK_REPO, cache_ratio=1.0)
    r.run_fixcache()
    print r.hit_count
    print r.miss_count

if __name__ == '__main__':
    sys.exit(main())
