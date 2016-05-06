#! /usr/bin/env python
"""Main analysis module."""
import constants
import os
import csv
import logging
import datetime
import daemon
import argparse
import repository
from repository import WindowedRepository

logger = logging.getLogger('fixcache_logger')


def evaluate_repository(repo_name, cache_ratio, pre_fetch_size,
                        distance_to_fetch,
                        version, **kwargs):
    """Evaluate a repository and save the evaluation results."""
    try:
        repo = WindowedRepository(
            repo_dir=constants.REPO_DICT[repo_name],
            cache_ratio=cache_ratio,
            pre_fetch_size=pre_fetch_size,
            distance_to_fetch=distance_to_fetch,
            **kwargs)
    except KeyError:
        print("Error: the requested repository does not exists." +
              "Please update constants.py")
        return
    except repository.RepositoryError as re:
        print(re)
        return

    dir_ = os.path.join(
        constants.CSV_ROOT, 'version_' + str(version), repo_name)

    if not os.path.exists(dir_):
        os.makedirs(dir_)

    file_ = os.path.join(dir_, 'evaluate_%s_cr_%s_pfs_%s_dtf_%s.csv' % (
        repo_name, cache_ratio, pre_fetch_size, distance_to_fetch))

    file_metadata = os.path.join(
        dir_,
        'evaluate_%s_cr_%s_pfs_%s_dtf_%s_metadata.csv' % (
            repo_name, cache_ratio, pre_fetch_size, distance_to_fetch))

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


def main(args):
    """Main entry."""
    evaluate_repository(
        repo_name=args.repository, pre_fetch_size=args.pfs,
        distance_to_fetch=args.dtf, cache_ratio=args.cr,
        version=constants.CURRENT_VERSION, branch=args.b)


parser = argparse.ArgumentParser(
    description='Run FixCache evaluation for different repos')

parser.add_argument('-d', '-daemon', action='store_true')
parser.add_argument('repository', metavar='repo')
parser.add_argument('--cr', '--cache_ratio', type=float, required=True)
parser.add_argument('--pfs', '--pre_fetch_size', type=float, required=True)
parser.add_argument('--dtf', '--distance_to_fetch', type=float, required=True)
parser.add_argument('--b', '--branch', type=str, default='master')
parser.add_argument('--logging', default='info')


if __name__ == '__main__':
    args = parser.parse_args()

    if args.logging == 'info':
        logger.setLevel(logging.INFO)
    elif args.logging == 'debug':
        logger.setLevel(logging.DEBUG)

    if args.d:
        with daemon.DaemonContext():
            main(args)
    else:
        main(args)
