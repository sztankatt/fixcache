#! /usr/bin/env python
"""Test analyses."""

from repository import RandomRepository
import constants
import timeit
import logging


logger = logging.getLogger('fixcache_logger')


def main():
    """Main entry for test_analysis.py."""
    logger.setLevel(logging.DEBUG)
    repo = RandomRepository(
        repo_dir=constants.FACEBOOK_SDK_REPO,
        cache_ratio=0.3,
        branch='master')

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time

    print repo.distance_to_fetch
    print repo.pre_fetch_size
if __name__ == '__main__':
    main()
