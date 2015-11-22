#! /usr/bin/env python
import os
import re
import datetime
import sys
from git import Repo
from db import DB, Commit, File, Change

join = os.path.join
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = join(BASE_DIR, 'repos')
FACEBOOK_SDK_REPO = join(REPO_DIR, 'facebook-sdk')
sys.path.append(join(BASE_DIR, 'fixcache'))


class Repository():
    def __init__(self, repo_dir):
        self.database = DB('sqlite:///fixcache.db')
        self.session = self.database.setup()

        try:
            repo = Repo(FACEBOOK_SDK_REPO)
            assert not repo.bare
            merge_commit_num = 0
            commit_list = repo.iter_commits()

            for commit in commit_list:
                num_parents = len(commit.parents)
                if num_parents == 0:
                    print "initial"
                elif num_parents == 1:
                    c = self.parse_commit(commit)
                    self.session.add(c)
                    blob_list = self.get_diff_file_list(
                        commit.parents[0], commit)
                    for change_type, blob in blob_list:
                        f = self.get_or_create_file(blob)
                        chg = Change(commit=c, file=f, change_type=change_type)
                        self.session.add(chg)
                else:
                    print "merged"
                    merge_commit_num += 1

            self.merge_commit_num = merge_commit_num
            self.session.commit()
        except Exception as e:
            raise e

    def is_fix_commit(self, commit):
        """returns True if commit object is flagged as fixing"""
        m = commit.message
        regex = r'[Ff][Ii][Xx]([Ee][Ss])*'
        if re.search(regex, m) is not None:
            return True
        else:
            return False

    def get_diff_file_list(self, commit1, commit2):
        """returns a list of blobs which changed from commit1 to commit2"""
        diffs = commit1.diff(commit2)
        file_list = []
        for diff in diffs:
            if diff.a_blob is None and diff.b_blob is not None:
                # new file
                file_list.append(('creation', diff.b_blob))
            elif diff.a_blob is not None and diff.b_blob is None:
                # deleted file
                file_list.append(('deletion', diff.a_blob))
            else:
                # changed file
                file_list.append(('change', diff.b_blob))

        return file_list

    def get_commit_tree_files(self, commit):
        """returns a list of blobs for a given commit"""
        file_list = []
        for item in commit.tree.traverse():
            if item.type == 'blob':
                # probably not the best way, as O(n^2) for the function
                file_list.append(item.new_file)

        return file_list

    def parse_commit(self, commit):
        return Commit(
            pushed_time=datetime.datetime.fromtimestamp(
                commit.committed_date),
            is_fix=self.is_fix_commit(commit))

    def get_or_create_file(self, blob):
        file_list = self.session.query(File).filter(
            File.path == blob.path).all()

        if len(file_list) == 0:
            f = File(path=blob.path)
            self.session.add(f)
        else:
            f = file_list[0]

        return f

    def get_commit_num(self):
        commit_num = self.session.query(Commit).count()
        commit_num += self.merge_commit_num
        return commit_num

r = Repository(FACEBOOK_SDK_REPO)
print r.get_commit_num()
r.database.teardown()
