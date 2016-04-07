#! /usr/bin/env python
"""Test analyses."""

from repository import Repository
import constants
import timeit
import logging


logger = logging.getLogger('fixcache_logger')


def main():
    """Main entry for test_analysis.py."""
    logger.setLevel(logging.INFO)
    repo = Repository(
        repo_dir=constants.BOTO_REPO,
        cache_ratio=.3,
        branch='develop',
        pre_fetch_size=0.1,
        distance_to_fetch=0.5)

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time
    print repo.hit_count
    print repo.miss_count
if __name__ == '__main__':
    main()
