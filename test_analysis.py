#! /usr/bin/env python
"""Test analyses."""

from repository import Repository
import constants
import timeit
import sys


def main():
    """Main entry for test_analysis.py."""
    facebook_sdk_repo = Repository(
        repo_dir=constants.FACEBOOK_SDK_REPO,
        cache_ratio=0.2,
        distance_to_fetch=0.5,
        pre_fetch_size=0.1)

    repo = facebook_sdk_repo
    time = timeit.timeit(repo.run_fixcache, number=1)
    print time
if __name__ == '__main__':
    sys.exit(main())
