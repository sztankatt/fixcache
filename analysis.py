#! /usr/bin/env python
from repository import Repository
from daemonize import Daemonize
import constants
import timeit
import os
import csv
import logging
import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler(constants.LOGFILE, "w")
fh.setLevel(logging.INFO)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]


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


def analyse_by_cache_ratio(repo, dtf, pfs, progressive=True):
    logger.info(
        "Starting fixcache analysis for %s with dtf=%s, pfs=%s, at %s" %
        (repo.repo_dir, dtf, pfs, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, repo.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    if progressive:
        file_ = os.path.join(
            dir_, ('analyse_by_cache_ratio_progressive_dtf_' + str(dtf) +
                   '_pfs_' + str(pfs) + '.csv')
        )
    else:
        file_ = os.path.join(
            dir_, ('analyse_by_cache_ratio_' + str(dtf) + '_pfs_' + str(pfs) +
                   '.csv'))

    if os.path.exists(file_):
        logger.info('Analysis exists.\nExit\n')
        return

    cache_ratio_range = [(x + 1) / 100.0 for x in range(100)]
    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(
            ['repo_dir', 'hits', 'misses', 'cache_size', 'dtf', 'pfs', 'ttr'])
        for ratio in cache_ratio_range:
            logging.debug(
                ('Running fixcache for %s with ratio of %s and dtf of %s, ' +
                 'with pfs of %s') %
                (repo.repo_dir, ratio, dtf, pfs))

            csv_out.writerow(basic_fixcache_analyser(
                repo, ratio, dtf, pfs))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def analyse_by_pfs_dtf(repo, cache_ratio, pfs_set, dtf_set):
    """Analyse by pfs and dtf."""
    logger.info(
        "Starting fixcache for fixed cache of %s at %s" %
        (cache_ratio, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, repo.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    file_ = os.path.join(
        dir_, 'analyse_by_fixed_cache_%s.csv' % (cache_ratio,))

    if os.path.exists(file_):
        logger.info('Analysis exists.\nExit\n')
        return

    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(
            ['repo_dir', 'hits', 'misses', 'cache_size', 'dtf', 'pfs', 'ttr'])

        for pfs in pfs_set:
            for dtf in dtf_set:
                logging.info(
                    ('Running fixcache for %s with ratio of %s and dtf ' +
                     'of %s, with pfs of %s') %
                    (repo.repo_dir, cache_ratio, dtf, pfs))
                csv_out.writerow(basic_fixcache_analyser(
                    repo, cache_ratio, dtf, pfs))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def main():
    # facebook_sdk_repo = Repository(constants.FACEBOOK_SDK_REPO)
    boto3_repo = Repository(constants.BOTO3_REPO, branch='develop')
    # boto_repo = Repository(constants.BOTO_REPO, branch='develop')
    # raspberry_io_repo = Repository('raspberryio')

    # boto3 tests
    dtf_set = [(x + 1) * 5 / 100.0 for x in range(20)]
    pfs_set = [(x + 1) / 100.0 for x in range(20)]
    # for i in variables:
    #     for j in variables:
    #         analyse_by_cache_ratio(facebook_sdk_repo, dtf=i, pfs=j)

    # for i in variables:
    #     for j in variables:
    #         analyse_by_cache_ratio(boto3_repo, dtf=i, pfs=j)

    # for i in variables:
    #     for j in variables:
    #         analyse_by_cache_ratio(boto_repo, dtf=i, pfs=j)
    # for i in variables:
    #    for j in variables:
    #        analyse_by_cache_ratio(raspberry_io_repo, dtf=i, pfs=j)
    analyse_by_pfs_dtf(
        boto3_repo, cache_ratio=0.15, pfs_set=pfs_set, dtf_set=dtf_set)

    # analyse_by_cache_ratio(boto_repo, 1)
if __name__ == '__main__':
    pid = os.path.join(constants.BASE_DIR, 'fixcache3.pid')

    daemon = Daemonize(app="fixcache", pid=pid, action=main, keep_fds=keep_fds)
    daemon.start()
