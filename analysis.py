#! /usr/bin/env python
from repository import Repository
import numpy
import sys
import constants
import timeit
import os
import csv
import logging


def basic_fixcache_analyser(repo, cache_ratio, distance_to_fetch):
    repo.reset(cache_ratio, distance_to_fetch)
    time = timeit.timeit(repo.run_fixcache, number=1)

    return (
        repo.repo_dir,
        repo.hit_count,
        repo.miss_count,
        repo.cache.size,
        time)


def analyse_by_cache_ratio(r, dtf):
    dir_ = os.path.join(constants.CSV_ROOT, r.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    file_ = os.path.join(dir_, 'analyse_by_cache_ratio_'+str(dtf)+'.csv')
    cache_ratio_range = numpy.arange(0.01, 1.01, 0.01)
    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)

        for ratio in cache_ratio_range:
            logging.info(
                'Running fixcache for %s with ratio of %s and dtf of %s' %
                (r.repo_dir, ratio, dtf))

            csv_out.writerow(basic_fixcache_analyser(
                r, ratio, dtf))


def main():
    logging.basicConfig(level=logging.INFO)
    # r = Repository(constants.FACEBOOK_SDK_REPO)
    boto3_repo = Repository(constants.BOTO3_REPO, branch='develop')

    for i in range(1, 5):
        analyse_by_cache_ratio(boto3_repo, i)
    # boto_repo = Repository(constants.BOTO_REPO, branch='develop')
    # analyse_by_cache_ratio(boto_repo, 1)
if __name__ == '__main__':
    sys.exit(main())
