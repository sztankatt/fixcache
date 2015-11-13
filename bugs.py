#! /usr/bin/env python
import os
import re
import datetime
import sys
from git import Repo
from db import DB, Commit

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


def get_diff_file_list(diff):
    diff_list = diff
    return [x.a_path for x in diff_list]


repo = Repo(FACEBOOK_SDK_REPO)
assert not repo.bare

commit_list = list(repo.iter_commits())

try:
    database = DB('sqlite:///fixcache.db')
    session = database.setup()
    for c in commit_list:
        commit = Commit(
            pushed_time=datetime.datetime.fromtimestamp(c.committed_date),
            is_fix=is_fix_commit(c))
        session.add(commit)

    session.commit()
    print session.query(Commit).count()
except:
    pass
finally:
    database.teardown()
