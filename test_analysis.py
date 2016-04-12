#! /usr/bin/env python
"""Test analyses."""

from repository import Repository, RandomRepository
import constants
import timeit
import logging


logger = logging.getLogger('fixcache_logger')


def main():
    """Main entry for test_analysis.py."""
    logger.setLevel(logging.INFO)
    repo = RandomRepository(
        repo_dir=constants.RASPBERRYIO_REPO,
        cache_ratio=0.2,
        branch='master')

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
