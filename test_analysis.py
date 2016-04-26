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
    repo = Repository(
        repo_dir=constants.RASPBERRYIO_REPO,
        cache_ratio=0.2,
        branch='master',
        distance_to_fetch=0.1,
        pre_fetch_size=0.1)

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time
    print repo.hit_count
    print repo.miss_count
if __name__ == '__main__':
    main()
