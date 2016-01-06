#! /usr/bin/env python
import sys
import parsing
from git import Repo
from cache import File, Cache, Distance
from consants import FACEBOOK_SDK_REPO

class Repository():
    def __init__(self, repo_dir):
        self.file_distances = set()
        try:
            self.repo = Repo(repo_dir)
            assert not self.repo.bare
            self.commit_list = list(self.repo.iter_commits('master'))
            for commit in self.commit_list:
                parents = commit.parents
                if len(parents) == 1:
                    print self.get_diff_file_list(commit, parents[0])
                    break

                """For each fixing commit: check files in cache.
                If miss, get the bug introducing commits for that file,
                at the parents commit point in time.
                """

        except Exception as e:
            raise e

    def calculate_distances(self):
        assert self.commit_list is not None
        raise NotImplementedError

    def get_deleted_lines(self, diff_message):
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

    def get_line_introducting_commits(self, line_list, file, commit):
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
        for commit, lines in self.repo.blame(commit, file):
            commit_list += [(commit, x) for x in lines]

        for start_line, end_line in line_list:
            for commit, line in commit_list[start_line:end_line+1]:
                if parsing.important_line(line):
                    commit_set.append(commit)

        return set(commit_set)

    def get_diff_file_list(self, commit1, commit2):
        """returns a list of blobs which changed from commit1 to commit2

        :type commit1: Commit object
        :param commit1: The child commit, which is newer

        :type commit2: Commit object
        :param commit2: The parent commit, which is older

        :rtype: tuple of file, deleted lines and change type
        :return: Returns a list of tuples with specification as above
        """

        diffs = commit1.diff(commit2, create_patch=True, unified=True)

        deleted_lines = self.get_deleted_lines(diffs[0].diff.splitlines())

        file_list = []
        for diff in diffs:
            if diff.a_blob is None and diff.b_blob is not None:
                # new file
                file_list.append(('creation', diff.b_blob.path, deleted_lines))
            elif diff.a_blob is not None and diff.b_blob is None:
                # deleted file
                file_list.append(('deletion', diff.a_blob.path, deleted_lines))
            elif diff.a_blob is not None and diff.b_blob is not None:
                # changed file
                file_list.append(('change', diff.b_blob.path, deleted_lines))

        return file_list

    def get_commit_tree_files(self, commit):
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
                file_list.append(item.new_file)

        return file_list

    def get_number_of_files(self):
        """returns the number of files and head

        :rtype: int
        :return: the number of files at head
        """
        file_list = self.get_commit_tree_files(self.commit_list[0])

        return len(file_list)


def main():
    """Main entry point for the script."""
    r = Repository(FACEBOOK_SDK_REPO)
    r.get_line_introducting_commits([(1, 1)], '.travis.yml', 'HEAD')

if __name__ == '__main__':
    sys.exit(main())
