#! /usr/bin/env python
import parsing
import cache
import filemanagement as fm
import git
import logging
import itertools
import os
from constants import REPO_DIR


class RepositoryError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Repository(object):
    def __init__(self, repo_dir, cache_ratio=0.1,
                 distance_to_fetch=1, branch='master'):
        # initializing repository variables
        try:
            self.file_distances = fm.DistanceSet()
            self.file_set = fm.FileSet()
            self.commit_order = {}
            self.distance_to_fetch = distance_to_fetch
            self.cache_ratio = cache_ratio
            self.hit_count = 0
            self.miss_count = 0
            self.repo_dir = repo_dir

            repo_full_path = os.path.join(REPO_DIR, repo_dir)
            self.repo = git.Repo(repo_full_path)
            assert not self.repo.bare
            self.commit_list = list(reversed(
                list(self.repo.iter_commits(branch))))

            # initializing commit hash to order mapping
            self.cache = cache.SimpleCache(self._calc_cache_size())
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
        return self._cache_ratio

    @cache_ratio.setter
    def cache_ratio(self, value):
        if value < 0.01 or value > 1.0:
            raise ValueError("Cache ratio has to be between 0.01 or 1.00")
        self._cache_ratio = value

    @property
    def distance_to_fetch(self):
        return self._distance_to_fetch

    @distance_to_fetch.setter
    def distance_to_fetch(self, value):
        if value < 0:
            raise ValueError(
                'distance_to_fetch has to be a non-negative integer')
        self._distance_to_fetch = value

    def _calc_cache_size(self):
        cache_size = int(self.cache_ratio*float(
            self._get_file_count(self.commit_list[-1])))
        if cache_size <= 0:
            cache_size = 1
        return cache_size

    def reset(self, cache_ratio=None, distance_to_fetch=None):
        self.hit_count = 0
        self.miss_count = 0
        self.file_distances.reset()
        self.file_set.reset()
        cache_size = None
        if cache_ratio is not None:
            self.cache_ratio = cache_ratio
            cache_size = self._calc_cache_size()

        if distance_to_fetch is not None:
            self.distance_to_fetch = distance_to_fetch

        self.cache.reset(cache_size)

    def run_fixcache(self):
        for commit in self.commit_list:
            parents = commit.parents
            if len(parents) == 1:
                files = self._get_diff_file_list(commit, parents[0])
                created_files = filter(lambda x: x[0] == 'created', files)
                changed_files = filter(lambda x: x[0] == 'changed', files)

                self._update_distance_set(created_files+changed_files, commit)

                if parsing.is_fix_commit(commit.message):
                    for _, path, lines in changed_files:
                        file_ = self.file_set.get_file(path)
                        file_.fault(self.commit_order[commit.hexsha])
                        if self.cache.file_in(file_):
                            self.hit_count += 1
                        else:
                            self.miss_count += 1
                            self.cache.add(file_)

                            line_intr_c = self._get_line_introducing_commits(
                                lines, path, commit)

                            for c in line_intr_c:
                                cf = self.file_distances.get_closest_files(
                                    file_,
                                    self.distance_to_fetch,
                                    self.commit_order[c.hexsha])

                            self.cache.add_multiple(cf)
                else:
                    for _, path, lines in changed_files:
                        file_ = self.file_set.get_file(path)
                        file_.changed(self.commit_order[commit.hexsha])
                        self.cache.add(file_)

                for _, path, l in created_files:
                    f = self.file_set.get_file(path)
                    f.changed(self.commit_order[commit.hexsha])
                    self.cache.add(f)

            elif len(parents) == 0:
                # initial commit
                files = self._get_commit_tree_files(commit)
                self.cache.add_multiple(self.file_set.get_multiple(files))
            else:
                pass

    def _init_commit_order(self):
        commit_counter = 0
        for commit in self.commit_list:
            self.commit_order[commit.hexsha] = commit_counter
            commit_counter += 1

    def _update_distance_set(self, files, commit):
        files = [self.file_set.get_file(x[1]) for x in files]
        file_pairs = list(itertools.combinations(files, 2))

        for pair in file_pairs:
            self.file_distances.add_occurrence(
                *pair, commit=self.commit_order[commit.hexsha])

    def _get_file_count(self, commit):
        return len(self._get_commit_tree_files(commit))

    def _get_deleted_lines(self, diff_message):
        """returns the line numbers which were deleted by a commit
        This means, that these line numbers will have to be used
        with the previous diff.
        """
        lines = []
        for line in diff_message:
            change = parsing.get_deletes(line)
            if change is not None:
                lines.append(change)

        return lines

    def _get_line_count(self, file_, commit):
        line_count = 0
        for commit, lines in self.repo.blame(commit, file_):
            line_count += len(lines)

    def _get_line_introducing_commits(self, line_list, file_, commit):
        """Returns the set of commits which introduced lines in a file.
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
            print file_ + " " + commit.hexsha
        finally:
            pass

        for start_line, end_line in line_list:
            for commit, line in commit_list[start_line:start_line+end_line+1]:
                if parsing.important_line(line):
                    commit_set.append(commit)

        return set(commit_set)

    def _get_diff_file_list(self, commit1, commit2):
        """returns a list of blobs which changed from commit1 to commit2

        :type commit1: Commit object
        :param commit1: The child commit, which is newer

        :type commit2: Commit object
        :param commit2: The parent commit, which is older

        :rtype: tuple of file, deleted lines and change type
        :return: Returns a list of tuples with specification as above
        """

        diffs = commit2.diff(commit1, create_patch=True, unified=True)

        file_list = []
        for diff in diffs:
            deleted_lines = self._get_deleted_lines(diff.diff.splitlines())
            if diff.new_file:
                file_list.append(('created', diff.b_blob.path, deleted_lines))
            elif diff.deleted_file:
                file_list.append(('deleted', diff.a_blob.path, deleted_lines))
            elif diff.renamed:
                pass
            else:
                if diff.b_blob is not None:
                    file_list.append((
                        'changed', diff.b_blob.path, deleted_lines))
                elif diff.a_blob is not None:
                    file_list.append((
                        'changed', diff.a_blob.path, deleted_lines))
        return file_list

    def _get_commit_tree_files(self, commit):
        """returns a list of blobs for a given commit

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
        """returns the number of files and head

        :rtype: int
        :return: the number of files at head
        """
        file_list = self._get_commit_tree_files(self.commit_list[0])

        return len(file_list)


# def main():
#     """Main entry point for the script."""
#     r = Repository(FACEBOOK_SDK_REPO, cache_ratio=0.1)
#     # hit_count, miss_count = r.run_fixcache()
#     print timeit.timeit(r.run_fixcache, number=1)
#     print r.hit_count
#     print r.miss_count

#     r.reset(cache_ratio=0.5)
#     r.run_fixcache()

#     print r.hit_count
#     print r.miss_count
#     # print hit_count, miss_count

# if __name__ == '__main__':
#     sys.exit(main())
