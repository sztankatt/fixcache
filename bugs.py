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


def is_fix_commit(commit):
    m = commit.message
    regex = r'[Ff][Ii][Xx]([Ee][Ss])*'
    if re.search(regex, m) is not None:
        return True
    else:
        return False


def get_diff_file_list(commit1, commit2):
    """returns a list of blobs from the commit1, which changed since commit2"""
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


def get_commit_tree_files(commit):
    """returns a list of blobs for the given commit"""
    file_list = []
    for item in commit.tree.traverse():
        if item.type == 'blob':
            # probably not the best way, as O(n^2) for the function
            file_list.append(item.new_file)

    return file_list


def parse_commit(commit):
    return Commit(
        pushed_time=datetime.datetime.fromtimestamp(
            commit.committed_date),
        is_fix=is_fix_commit(commit))


def get_or_create_file(session, blob):
    file_list = session.query(File).filter(
        File.path == blob.path).all()

    if len(file_list) == 0:
        f = File(path=blob.path)
        session.add(f)
        session.commit()
    else:
        f = file_list[0]

    return f


repo = Repo(FACEBOOK_SDK_REPO)
assert not repo.bare

commit_list = repo.iter_commits()

try:
    database = DB('sqlite:///fixcache.db')
    session = database.setup()
    for commit in commit_list:
        num_parents = len(commit.parents)
        if num_parents == 0:
            print "initial"
        elif num_parents == 1:
            c = parse_commit(commit)
            session.add(c)
            blob_list = get_diff_file_list(commit.parents[0], commit)
            for change_type, blob in blob_list:
                f = get_or_create_file(session, blob)
                chg = Change(commit=c, file=f, change_type=change_type)
                session.add(chg)
            session.commit()

        else:
            print "merged"

            session.commit()

        # testing
    print session.query(Commit).order_by(Commit.pushed_time).all()

except Exception as e:
    raise e
finally:
    database.teardown()
