#! /usr/bin/env python
"""Main analysis module."""
from repository import Repository
import constants
import timeit
import os
import sys
import csv
import logging
import datetime
import daemon


logger = logging.getLogger('fixcache_logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(constants.LOGFILE, "w")
fh.setLevel(logging.INFO)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]


def basic_fixcache_analyser(repo, cache_ratio, distance_to_fetch, pfs):
    """Basic analyser, used for one line in the csv files."""
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


def analyse_by_cache_ratio(version, repo, dtf, pfs, progressive=True):
    """Analyse a repository by cache ratio, with given pfs and dtf."""
    logger.info(
        "Starting fixcache analysis for %s with dtf=%s, pfs=%s, at %s" %
        (repo.repo_dir, dtf, pfs, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, version, repo.repo_dir)

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


def analyse_by_pfs_dtf(version, repo, cache_ratio, pfs_set, dtf_set):
    """Analyse with fixed cache ratio, varying pfs and dtf."""
    logger.info(
        "Starting fixcache for fixed cache of %s at %s" %
        (cache_ratio, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, version, repo.repo_dir)

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


def main(*args):
    """Main entry."""
    if args[0] == 'facebook-sdk':
        repo = Repository(constants.FACEBOOK_SDK_REPO)
    elif args[0] == 'boto3':
        repo = Repository(constants.BOTO3_REPO, branch='develop')
    elif args[0] == 'boto':
        repo = Repository(constants.BOTO_REPO, branch='develop')
    elif args[0] == 'raspberrio':
        repo = Repository('raspberryio')

    # boto3 tests
    dtf_set = [0.1, 0.2, 0.3, 0.4, 0.5]
    pfs_set = [0.1, 0.15, 0.2]
    for i in dtf_set:
        for j in pfs_set:
            analyse_by_cache_ratio(args[1], repo, dtf=i, pfs=j)

if __name__ == '__main__':
    with daemon.DaemonContext():
        main(*sys.argv[1:])
    # daemon = Daemonize(
    #     app="fixcache",
    #     pid=pid, action=main(*sys.argv[1:]), keep_fds=keep_fds)
    # daemon.start()
