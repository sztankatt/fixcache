#! /usr/bin/env python
"""Test analyses."""

from repository import Repository
import constants
import timeit
import logging


def main():
    """Main entry for test_analysis.py."""
    logger = logging.getLogger('fixcache_logger')
    logger.setLevel(logging.DEBUG)
    repo = Repository(
        repo_dir=constants.BOTO_REPO,
        distance_to_fetch=0.1,
        pre_fetch_size=0.2,
        cache_ratio=0.2,
        branch='develop')

    time = timeit.timeit(repo.run_fixcache, number=1)
    print time
if __name__ == '__main__':
    main()
