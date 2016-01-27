#! /usr/bin/env python
from repository import Repository
import numpy
import sys
import constants
import timeit
import os
import csv
import logging


def basic_fixcache_analyser(repo, cache_ratio, distance_to_fetch, pfs):
    repo.reset(cache_ratio, distance_to_fetch, pfs)
    time = timeit.timeit(repo.run_fixcache, number=1)

    return (
        repo.repo_dir,
        repo.hit_count,
        repo.miss_count,
        repo.cache.size,
        repo.distance_to_fetch,
        repo.pre_fetch_size,
        time)


def analyse_by_cache_ratio(r, dtf, pfs, progressive=False, filename=None):
    dir_ = os.path.join(constants.CSV_ROOT, r.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    if filename is None:
        if progressive:
            file_ = os.path.join(
                dir_, 'analyse_by_cache_ratio_progressive_dtf_'+str(dtf)+'_pfs_'+str(pfs)+'.csv')
        else:
            file_ = os.path.join(dir_, 'analyse_by_cache_ratio_'+str(dtf)+'_pfs_'+str(pfs)+'.csv')
    else:
        file_ = os.path.join(dir_, filename+str(dtf)+'.csv')
    cache_ratio_range = numpy.arange(0.01, 1.01, 0.01)
    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(
            ['repo_dir', 'hits', 'misses', 'cache_size', 'dtf', 'pfs', 'ttr'])
        for ratio in cache_ratio_range:
            logging.info(
                'Running fixcache for %s with ratio of %s and dtf of %s, with pfs of %s' %
                (r.repo_dir, ratio, dtf, pfs))

            csv_out.writerow(basic_fixcache_analyser(
                r, ratio, dtf, pfs))


def main():
    logging.basicConfig(level=logging.INFO)
    # r = Repository(constants.FACEBOOK_SDK_REPO)
    boto3_repo = Repository(constants.BOTO3_REPO, branch='develop')
    #boto_repo = Repository(constants.BOTO_REPO, branch='develop')
    for i in [0.1, 0.15, 0.2, 0.25]:
        analyse_by_cache_ratio(boto3_repo, i, pfs=i, progressive=True)

    # analyse_by_cache_ratio(boto_repo, 1)
if __name__ == '__main__':
    sys.exit(main())
