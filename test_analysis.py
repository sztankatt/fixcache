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
        repo_dir=constants.BOTO3_REPO,
        cache_ratio=1.0,
        pre_fetch_size=0.1,
        distance_to_fetch=0.5,
        branch='develop')

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time
    print repo.cache_size
    print repo.cache_ratio
    print repo.distance_to_fetch
    print repo.pre_fetch_size
    print repo.hit_count
    print repo.miss_count
if __name__ == '__main__':
    main()
