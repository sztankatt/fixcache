#! /usr/bin/env python
import os
import datetime
import sys
from db import DB, Commit, File, Change

join = os.path.join
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = join(BASE_DIR, 'repos')
FACEBOOK_SDK_REPO = join(REPO_DIR, 'facebook-sdk')
sys.path.append(join(BASE_DIR, 'fixcache'))


def test():
    try:
        database = DB('sqlite:///fixcache_test.db')
        session = database.setup()
        f = File(path='aa')
        f2 = File(path='bb')
        c = Commit(is_fix=False, pushed_time=datetime.datetime.now())
        chg = Change(file=f, commit=c, change_type='creation')
        chg2 = Change(file=f2, commit=c, change_type='creation')
        session.add(f)
        session.add(f2)
        session.add(c)
        session.add(chg)
        session.add(chg2)
        session.commit()

        c = session.query(Commit).all()[0]
        print [chg.file for chg in c.change]
    except Exception as e:
        raise e
    finally:
        database.teardown()
test()
