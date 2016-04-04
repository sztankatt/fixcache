#! /usr/bin/env python
"""Main analysis module."""
from repository import Repository, WindowedRepository, RandomRepository
import constants
import timeit
import os
import sys
import csv
import logging
import datetime
import daemon
import argparse

from constants import CURRENT_VERSION
from helper_functions import DeprecatedError


logger = logging.getLogger('fixcache_logger')
logger.setLevel(logging.DEBUG)


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
                repo, ratio, distance_to_fetch=distance_to_fetch,
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
                    repo, cache_ratio, dtf, pfs))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def evaluate_repository(repo_name, cache_ratio, pfs, dtf,
                        version, **kwargs):
    """Evaluate a repository and save the evaluation results."""
    print cache_ratio
    repo = WindowedRepository(
        repo_dir=constants.REPO_DICT[repo_name],
        cache_ratio=cache_ratio,
        pre_fetch_size=pfs,
        distance_to_fetch=dtf,
        **kwargs)

    dir_ = os.path.join(constants.CSV_ROOT, version, repo.repo_dir)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    file_ = os.path.join(dir_, 'evaluate_%s_cr_%s_pfs_%s_dtf_%s.csv' % (
        repo_name, cache_ratio, pfs, dtf))

    file_metadata = os.path.join(
        dir_,
        'evaluate_%s_cr_%s_pfs_%s_dtf_%s_metadata.csv' % (
            repo_name, cache_ratio, pfs, dtf))

    if os.path.exists(file_) and os.path.exists(file_metadata):
        logger.info('Evaluation exists.\nExit\n')
        return True

    cache_size = repo.cache_size
    commit_num = len(repo.commit_list) + len(repo.horizon_commit_list)
    file_count = repo.file_count

    values = repo.evaluate()

    with open(file_metadata, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['cache_size', 'commit_num', 'file_count'])
        csv_out.writerow([cache_size, commit_num, file_count])

    with open(file_, 'wb') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['counter', 'true_positive', 'false_positive',
                          'true_negative', 'false_negative', 'file_count',
                          'hexsha'])

        for line in values:
            csv_out.writerow(line)

    logger.info("Evaluation finished at %s\n" % (
        datetime.datetime.now(),))

    return True


def random_cache_analyser(repo_name, **kwargs):
    """Analyse a repository by cache ratio, with given pfs and dtf."""
    logger.info(
        "Starting fixcache analysis for %s with random cache, at %s" %
        (repo_name.repo_dir, datetime.datetime.now()))
    dir_ = os.path.join(constants.CSV_ROOT, 'random', repo_name.repo_dir)

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
                repo_name, ratio, pfs=0, distance_to_fetch=0))

    logger.info("Analysis finished at %s\n" % (datetime.datetime.now(),))


def main(parser):
    """Main entry."""
    args = parser.parse_args()

    if args.function == 'random_cache_analyser':
        repo = RandomRepository(args.repository)
        random_cache_analyser(repo)
    else:
        if args.v != CURRENT_VERSION:
            parser.error('Version has to be %s' % (CURRENT_VERSION,))
        else:
            version = 'version_' + str(CURRENT_VERSION)
            repo = Repository(args.repository)

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
                        version=version, repo_name=repo,
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
parser.add_argument('--v', '--version', type=int)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.d:
        with daemon.DaemonContext():
            main(parser)
    else:
        main(parser)
