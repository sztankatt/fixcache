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
        repo_dir=constants.DJANGO_REPO,
        cache_ratio=0.3,
        branch='master')

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time

    print repo.distance_to_fetch
    print repo.pre_fetch_size
if __name__ == '__main__':
    main()
