#! /usr/bin/env python
"""Main analysis module."""
import timeit
import constants
import os
import csv
import logging
import datetime
import daemon
import argparse
from repository import RandomRepository, Repository

from constants import CURRENT_VERSION


logger = logging.getLogger('fixcache_logger')


def basic_fixcache_analyser(repo, *args, **kwargs):
    """Basic analyser, used for one line in the csv files."""
    repo.reset(*args, **kwargs)
    time = timeit.timeit(repo.run_fixcache, number=1)

    return (
        repo.repo_dir,
        repo.hit_count,
        repo.miss_count,
        repo.cache_size,
        repo.distance_to_fetch,
        repo.pre_fetch_size,
        time)


def analyse_by_cache_ratio(version, repo, distance_to_fetch,
                           pre_fetch_size, progressive=True):
    """Analyse a repository by cache ratio, with given pfs and dtf."""
    logger.info(
        "Starting fixcache analysis for %s with dtf=%s, pfs=%s, at %s" %
        (repo.repo_dir, distance_to_fetch,
         pre_fetch_size, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, version, repo.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    if progressive:
        file_ = os.path.join(
            dir_, ('analyse_by_cache_ratio_progressive_dtf_' +
                   str(distance_to_fetch) +
                   '_pfs_' + str(pre_fetch_size) + '.csv')
        )
    else:
        file_ = os.path.join(
            dir_, ('analyse_by_cache_ratio_' + str(distance_to_fetch) +
                   '_pfs_' + str(pre_fetch_size) +
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
                (repo.repo_dir, ratio, distance_to_fetch, pre_fetch_size))

            csv_out.writerow(basic_fixcache_analyser(
                repo=repo, cache_ratio=ratio,
                distance_to_fetch=distance_to_fetch,
                pre_fetch_size=pre_fetch_size))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def analyse_by_fixed_cache_ratio(version, repo, cache_ratio, pfs_set, dtf_set):
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
                    repo=repo, cache_ratio=cache_ratio, distance_to_fetch=dtf,
                    pre_fetch_size=pfs))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def random_cache_analyser(repo, **kwargs):
    """Analyse a repository by cache ratio, with given pfs and dtf."""
    logger.info(
        "Starting fixcache analysis for %s with random cache, at %s" %
        (repo.repo_dir, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, 'random', repo.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    file_ = os.path.join(
        dir_, ('analyse_by_random_cache.csv'))

    if os.path.exists(file_):
        logger.info('Analysis exists.\nExit\n')
        return

    cache_ratio_range = [(x + 1) / 100.0 for x in range(100)]
    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(
            ['repo_dir', 'hits', 'misses', 'cache_size', 'dtf', 'pfs', 'ttr'])
        for ratio in cache_ratio_range:

            csv_out.writerow(basic_fixcache_analyser(
                repo=repo, cache_ratio=ratio,
                pre_fetch_size=0, distance_to_fetch=0))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def main(parser):
    """Main entry."""
    args = parser.parse_args()

    if args.function == 'random_cache_analyser':
        repo = RandomRepository(repo_dir=args.repository, branch=args.b)
        random_cache_analyser(repo)
    else:
        if args.v != CURRENT_VERSION:
            parser.error('Version has to be %s' % (CURRENT_VERSION,))
        else:
            version = 'version_' + str(CURRENT_VERSION)
            repo = Repository(args.repository, branch=args.b)

            if args.function == 'analyse_by_cache_ratio':
                dtf_set = [0.1, 0.2, 0.3, 0.4, 0.5]
                pfs_set = [0.1, 0.15, 0.2]
                for i in dtf_set:
                    for j in pfs_set:
                        analyse_by_cache_ratio(
                            version=version, repo=repo, distance_to_fetch=i,
                            pre_fetch_size=j)
            elif args.function == 'analyse_by_fixed_cache_ratio':
                # dtf_set = [0.1, 0.15, 0.2, .., 0.55]
                dtf_set = [float(x + 2) / 20 for x in range(10)]
                # pfs_set = [0.1, 0.15, ..., 0.35]
                pfs_set = dtf_set[:6]
                # cache_ratio = [0.05, 0.1, 0.15, ..., 0.5]
                cache_ratio = [float(x + 1) / 20 for x in range(10)]

                for cr in cache_ratio:
                    analyse_by_fixed_cache_ratio(
                        version=version, repo=repo,
                        cache_ratio=cr, dtf_set=dtf_set, pfs_set=pfs_set)
            elif args.function == 'analyse_single':
                if args.pfs is None or args.dtf is None:
                    parser.error('pfs and dtf has to be set')
                else:
                    analyse_by_cache_ratio(
                        version=version, repo=repo, pre_fetch_size=args.pfs,
                        distance_to_fetch=args.dtf)

ANALYSIS_CHOICES = [
    'analyse_by_cache_ratio',
    'analyse_single',
    'random_cache_analyser',
    'analyse_by_fixed_cache_ratio']

parser = argparse.ArgumentParser(
    description='Run FixCache analysis for different repos')

parser.add_argument('-d', '-daemon', action='store_true')
parser.add_argument(
    'function', metavar='fun', choices=ANALYSIS_CHOICES,
    help='function for an analysis')
parser.add_argument('repository', metavar='repo')
parser.add_argument('--cr', '--cache_ratio', type=float)
parser.add_argument('--pfs', '--pre_fetch_size', type=float)
parser.add_argument('--dtf', '--distance_to_fetch', type=float)
parser.add_argument('--b', '--branch', type=str, default='master')
parser.add_argument('--logging', default='info')
parser.add_argument('--v', '--version', type=int)


if __name__ == '__main__':
    args = parser.parse_args()

    if args.logging == 'info':
        logger.setLevel(logging.INFO)
    elif args.logging == 'debug':
        logger.setLevel(logging.DEBUG)

    if args.d:
        with daemon.DaemonContext():
            main(parser)
    else:
        main(parser)
