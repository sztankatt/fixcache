#! /usr/bin/env python
"""docstring."""
import argparse

import csv

import os

from evaluation import evaluate_repository

import constants

from constants import REPO_DATA, version_color, CURRENT_VERSION
# from graph_data import plot_1_data

import matplotlib.lines as mlines

import matplotlib.pyplot as plt

import numpy as np

import daemon

from pylab import text


fontsize = 20


def _file_to_csv_by_name(version, repo_name, file_):
    """Get the csv file to a list of rows, as tuples."""
    dir_ = os.path.join(constants.CSV_ROOT, version, repo_name)
    file_ = os.path.join(
        dir_, file_
    )
    try:
        print file_
        with open(file_, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            return [row for row in csv_reader]
    except:
        pass


def _file_to_csv(version, repo_name, pre_fetch_size, distance_to_fetch):
    """Read file into csv type python object."""
    file_ = ('analyse_by_cache_ratio_progressive_dtf_' +
             str(distance_to_fetch) + '_pfs_' + str(pre_fetch_size) + '.csv')

    return _file_to_csv_by_name(
        version=version, repo_name=repo_name, file_=file_)


def calc_hit_rate(x, y):
    """Calculate hit rate based on hit and miss value."""
    lookups = int(x) + int(y)
    hit_rate = float(x) / float(lookups)
    return hit_rate


def get_column(csv_reader, col_name):
    """Get column."""
    if csv_reader is not None:
        if col_name == 'hit_rate':
            return [calc_hit_rate(x['hits'], x['misses']) for x in csv_reader]
        else:
            return [x[col_name] for x in csv_reader]


def plot_several(pre_fetch_size, distance_to_fetch, version, figure_name=None):
    """Sample plot of several different repos."""
    x = range(100)
    legend = []

    fig, ax = plt.subplots(figsize=(19, 8))
    plt.tick_params(labelsize=fontsize)

    for repo_name in REPO_DATA:
        csv_reader = _file_to_csv(
            version=version,
            repo_name=repo_name, pre_fetch_size=pre_fetch_size,
            distance_to_fetch=distance_to_fetch)
        y = get_column(csv_reader, 'hit_rate')
        if y is not None and y != []:
            plt.plot([float(x1 + 1) / 100 for x1 in x],
                     y, color=REPO_DATA[repo_name]['color'], linewidth=3)
            line = mlines.Line2D(
                [], [], color=REPO_DATA[repo_name]['color'],
                label=REPO_DATA[repo_name]['legend'], linewidth=3)
            legend.append(line)

    plt.legend(handles=legend, loc=4, fontsize=fontsize)
    plt.ylabel('hit-rate', fontsize=fontsize)
    plt.xlabel('cache-ratio', fontsize=fontsize)
    plt.plot([0.1 for i in range(101)],
             [float(q) / 100 for q in range(101)],
             color='black', linestyle='-.')

    if figure_name is None:
        plt.title("FixCache for several repositories",
                  y=1.02, fontsize=fontsize)
    else:
        plt.title(figure_name)

    legend_text = 'pre-fetch-size = %s, distance-to-fetch = %s' % (
        pre_fetch_size, distance_to_fetch)
    text(0.985, 0.4, legend_text, ha='right', va='top',
         transform=ax.transAxes, multialignment='left', fontsize=fontsize,
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    fig.tight_layout()
    ax.set_ylim(0.0, 1.05)
    plt.show()


def plot_one(repo_name, pre_fetch_size,
             distance_to_fetch, version, fig_name=None):
    """Plot a single repository data."""
    x = range(100)
    print "a"
    csv_reader = _file_to_csv(version=version, repo_name=repo_name,
                              pre_fetch_size=pre_fetch_size,
                              distance_to_fetch=distance_to_fetch)
    csv_random_file = _file_to_csv_by_name(
        'random',
        repo_name,
        'analyse_by_random_cache.csv')

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader, 'hit_rate')

    fig, ax = plt.subplots()

    fig.suptitle(
        "Analysing fixcache for %s" % (repo_name + '.git',), fontsize=16,
        y=1.02)
    legend_text = 'pfs = %s, dtf = %s' % (
        pre_fetch_size, distance_to_fetch)
    text(0.55, 0.07, legend_text, ha='center', va='center',
         transform=ax.transAxes, multialignment='left',
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    ax.set_ylabel('hit rate')
    ax.set_xlabel('cache size')
    ax.grid(True)
    ax.plot(x, hit_rate, color='red', linewidth=2)

    if csv_random_file is not None:
        random_hit_rate = get_column(csv_random_file, 'hit_rate')
        ax.plot(x, random_hit_rate, color='blue', linewidth=2)

    plt.show()


def plot_all(repo_name, version):
    dtf_set = [0.1, 0.2, 0.3, 0.4, 0.5]
    pfs_set = [0.1, 0.15, 0.2]
    fontsize = 18
    fig, ax = plt.subplots()
    ax.set_ylim(0.0, 1.1)
    ax.set_xlim(0.0, 1.0)
    hit_rates = []
    for pfs in pfs_set:
        for dtf in dtf_set:
            csv_reader = _file_to_csv(
                version=version, repo_name=repo_name, distance_to_fetch=dtf,
                pre_fetch_size=pfs)
            if csv_reader is None:
                continue
            else:
                hit_rate = get_column(csv_reader, 'hit_rate')
                hit_rates.append(hit_rate)

    hit_rates = np.matrix(hit_rates)
    counter = 0.01
    avg = []
    diff = []
    for column in hit_rates.T:
        plt.plot([counter, counter], [column.min(), column.max()], linewidth=3,
                 color='k')
        counter += 0.01

        avg.append((column.max() + column.min()) / 2.0)
        diff.append(column.max() - column.min())

    print max(diff)
    print diff.index(max(diff))
    print diff[11]

    plt.tick_params(labelsize=fontsize)
    x = [float(x1 + 1) / 100 for x1 in range(100)]
    plt.plot(x, avg, color='k', linewidth=2)

    plt.title('All cache-ratio analyses for %s (#c=%s)' % (
        repo_name + '.git', REPO_DATA[repo_name]['commit_num']),
        fontsize=fontsize)
    plt.ylabel('hit-rate', fontsize=fontsize)
    plt.xlabel('cache-ratio', fontsize=fontsize)
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def plot_fixed_cache_ratio(repo_name, cache_ratio, version, fig_name=None):
    """Fixed cache rate plot, variable pfs and dtf."""
    csv_reader = csv_reader = _file_to_csv_by_name(
        version,
        repo_name,
        'analyse_by_fixed_cache_%s.csv' % (cache_ratio,))

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader=csv_reader, col_name='hit_rate')
    # cache_size = get_column(csv_reader, 'cache_size')[0]

    base = [float(x + 2) / 20 for x in range(10)]

    dtf_size = 6 * base
    pfs_size = []
    for i in base[:6]:
        pfs_size = pfs_size + 10 * [i]
    print len(pfs_size), len(dtf_size)

    fig, ax = plt.subplots(figsize=(10, 10))
    plt.tick_params(labelsize=fontsize)
    plt.grid(True)
    sc = plt.scatter(pfs_size, dtf_size, s=300,
                     color=[str(x) for x in hit_rate],
                     cmap=plt.cm.viridis_r, alpha=0.85)

    plt.title(
        'fixed cache-ratio of %s for %s.git' % (cache_ratio, repo_name,),
        fontsize=fontsize)

    plt.ylabel('distance-to-fetch', fontsize=fontsize)
    plt.xlabel('pre-fetch-size', fontsize=fontsize)

    axcb = fig.colorbar(sc)
    axcb.ax.tick_params(labelsize=fontsize)
    axcb.set_label('Hit rate', fontsize=fontsize)
    ax.set_ylim(0.05, 0.6)
    ax.set_xlim(0.075, 0.375)
    fig.tight_layout()
    plt.show()


def plot_different_versions(repo_name, pre_fetch_size, distance_to_fetch,
                            fig_name=None):
    """Sample plot of several different repos."""
    x = range(100)
    legend = []

    fig, ax = plt.subplots()

    for version in version_color:
        csv_reader = _file_to_csv(
            version=version, repo_name=repo_name,
            pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch)

        y = get_column(csv_reader, 'hit_rate')
        if y is not None:
            plt.plot(x, y, color=version_color[version])
            line = mlines.Line2D(
                [], [],
                label=version, color=version_color[version], linewidth=2)
            legend.append(line)

    plt.title('Different version outputs of %s.git' % (repo_name,),
              y=1.02)

    plt.legend(handles=legend, loc=4)
    plt.ylabel('hit rate')
    plt.xlabel('cache size (%)')
    legend_text = 'pfs = %s, dtf = %s\ncommit_num = %s' % (
        pre_fetch_size, distance_to_fetch, REPO_DATA[repo_name]['commit_num'])
    text(0.55, 0.07, legend_text, ha='center', va='center',
         transform=ax.transAxes, multialignment='left',
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def plot_speedup(repo_name, pre_fetch_size, distance_to_fetch, versions):
    """Speedup plot."""
    x = [float(p + 1) / 100 for p in range(100)]
    legend = []
    if len(versions) != 2:
        return
    csv_reader1 = _file_to_csv(
        version=versions[0], repo_name=repo_name,
        pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch)
    y1 = get_column(csv_reader1, 'ttr')

    csv_reader2 = _file_to_csv(
        version=versions[1], repo_name=repo_name,
        pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch)

    y2 = get_column(csv_reader2, 'ttr')

    fig, ax = plt.subplots(figsize=(20, 7))
    plt.tick_params(labelsize=fontsize)

    if y1 is not None and y2 is not None:
        plt.plot(x, y1, color='blue', linewidth=2)
        plt.plot(x, y2, color='red', linewidth=2)

        line = mlines.Line2D(
            [], [], color='blue',
            label=versions[0], linewidth=2)
        line2 = mlines.Line2D(
            [], [], color='red',
            label=versions[1], linewidth=2)

        legend.append(line)
        legend.append(line2)

    plt.legend(handles=legend, fontsize=fontsize)

    plt.title('Speedup of %s.git from %s to %s' % (
        repo_name, versions[0], versions[1]),
        y=1.02, fontsize=fontsize)
    plt.ylabel('Time-to-run (s)', fontsize=fontsize)
    plt.xlabel('cache ratio', fontsize=fontsize)
    legend_text = (
        'pre-fetch-size = %s, distance-to-fetchf = %s\n' +
        'commit_num = %s') % (
            pre_fetch_size,
            distance_to_fetch, REPO_DATA[repo_name]['commit_num'])
    text(0.82, 0.96, legend_text, ha='right', va='top',
         transform=ax.transAxes, multialignment='left', fontsize=fontsize,
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    fig.tight_layout()
    plt.show()


def _label_rects(rects, annotation, ax):
    for counter, rect in enumerate(rects):
        print annotation[counter]
        height = rect.get_height()
        print height
        ax.text(
            rect.get_x() + rect.get_width() / 2., 1.01,
            '%d' % int(annotation[counter]),
            ha='center', va='bottom', fontsize=fontsize)


def _get_statistics(repo_name, cache_ratio, pre_fetch_size, distance_to_fetch,
                    version, branch, n=10, **kwargs):
    if evaluate_repository(repo_name, float(cache_ratio),
                           float(pre_fetch_size), float(distance_to_fetch),
                           version, branch=branch, **kwargs):

        csv_reader = _file_to_csv_by_name(
            version=version, repo_name=repo_name,
            file_='evaluate_%s_cr_%s_pfs_%s_dtf_%s.csv' % (
                repo_name, cache_ratio, pre_fetch_size, distance_to_fetch))
        true_positive = get_column(csv_reader, 'true_positive')[:n]
        false_positive = get_column(csv_reader, 'false_positive')[:n]
        true_negative = get_column(csv_reader, 'true_negative')[:n]
        false_negative = get_column(csv_reader, 'false_negative')[:n]
        file_count = get_column(csv_reader, 'file_count')[:n]
        counter = get_column(csv_reader, 'counter')[:n]

        n = len(counter)

        true_positive = np.array([float(i) for i in true_positive])
        false_positive = np.array([float(i) for i in false_positive])
        true_negative = np.array([float(i) for i in true_negative])
        false_negative = np.array([float(i) for i in false_negative])
        file_count = np.array([float(i) for i in file_count])

        return (true_positive, false_positive, true_negative, false_negative,
                file_count, counter)


def evaluation_comparison(repo_name, version,
                          pre_fetch_size=0.1, distance_to_fetch=0.5,
                          branch='master', **kwargs):

    fontsize = 18
    figsize = 18, 9
    n = 30
    f_beta = 2
    (tp_01, fp_01, tn_01, fn_01, fc_01, counter_01) = _get_statistics(
        repo_name=repo_name, cache_ratio=0.1,
        pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch,
        version=version, n=n, branch=branch, **kwargs)

    (tp_02, fp_02, tn_02, fn_02, fc_02, counter_02) = _get_statistics(
        repo_name=repo_name, cache_ratio=0.2,
        pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch,
        version=version, n=n, branch=branch, **kwargs)

    ind = np.arange(len(counter_01))
    linewidth = 3
    fig, ax = plt.subplots(figsize=figsize)
    plt.locator_params(axis='x', nbins=n)
    ax.set_ylim(0.0, 1.1)
    precision_01 = tp_01 / (tp_01 + fp_01)
    recall_01 = tp_01 / (tp_01 + fn_01)
    f1_01 = (1 + f_beta**2) * tp_01 / (
        (1 + f_beta**2) * tp_01 + f_beta**2 * fn_01 + fp_01)

    precision_02 = tp_02 / (tp_02 + fp_02)
    recall_02 = tp_02 / (tp_02 + fn_02)
    f1_02 = (1 + f_beta**2) * tp_02 / (
        (1 + f_beta**2) * tp_02 + f_beta**2 * fn_02 + fp_02)

    ax.set_xticklabels(counter_01)
    plt.plot(ind, precision_01, '--', label='Precision (cr=0.1)',
             color='green', linewidth=linewidth)
    plt.plot(ind, precision_02,
             color='green', linewidth=linewidth, label='Precision (cr=0.2)')

    plt.plot(ind, f1_01, '--', color='orange', linewidth=linewidth,
             label=r'$F_2$ score (cr=0.1)')
    plt.plot(ind, f1_02, color='orange', linewidth=linewidth,
             label=r'$F_2$ score (cr=0.2)')

    plt.plot(ind, recall_01, '--', color='blue', linewidth=linewidth,
             label='Recall (cr=01)')
    plt.plot(ind, recall_02, color='blue', linewidth=linewidth,
             label='Recall (cr=0.2)')

    plt.grid(True)
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0., fontsize=fontsize)
    plt.title('Evaluating %s.git' % (repo_name,), fontsize=fontsize, y=1.15)
    fig.subplots_adjust(top=0.8)
    plt.tick_params(labelsize=fontsize)
    plt.xlabel('Fixing commit numbers after tNow*0.9', fontsize=fontsize)
    fig.tight_layout()
    plt.show()


def evaluation(repo_name, cache_ratio, pre_fetch_size, distance_to_fetch,
               version, branch='master', **kwargs):
    """Evaluate a repository, produce an evaluation graph."""
    n = 10
    width = 0.25
    y_lim = 1.5
    figsize = 18, 9

    (true_positive, false_positive, true_negative, false_negative,
     file_count, counter) = _get_statistics(
        repo_name=repo_name, cache_ratio=cache_ratio,
        pre_fetch_size=pre_fetch_size, distance_to_fetch=distance_to_fetch,
        version=version, n=n, branch=branch, **kwargs)

    ind = np.arange(n)

    # figure 1 data
    precision = true_positive / (true_positive + false_positive)
    f_discovery_rate = false_positive / (true_positive + false_positive)
    n_predictive_value = true_negative / (true_negative + false_negative)
    f_omission_rate = false_negative / (true_negative + false_negative)

    # figure 2 data
    accuracy = (true_positive + true_negative) / (
        true_positive + true_negative + false_negative + false_positive)
    f1_score = 2 * true_positive / (
        2 * true_positive + false_negative + false_positive)

    # figure 3 data
    sensitivity = true_positive / (true_positive + false_negative)
    specificity = true_negative / (true_negative + false_positive)

    # figure 4 data
    # figure 1
    fig, ax = plt.subplots(figsize=figsize)
    # settings
    ax.set_xticks(ind + width)
    ax.set_xticklabels(counter)
    ax.set_ylim(0.0, y_lim)
    # plt.ylabel('ratio', fontsize=fontsize)
    plt.xlabel('10 bug-fixing commits after stopping FixCache at tHStart',
               fontsize=fontsize)
    plt.title("TP, FP, TN and FN values for %s.git" % (repo_name,),
              y=1.02, fontsize=fontsize)
    plt.grid(True)

    # showing the bars
    p1 = plt.bar(ind, precision, width, color='#0FCC1B')
    p2 = plt.bar(
        ind, f_discovery_rate, width, color='#CC8800', bottom=precision)
    p3 = plt.bar(ind + width, n_predictive_value, width, color='#0369CC')
    p4 = plt.bar(ind + width, f_omission_rate, width, color='#CC0200',
                 bottom=n_predictive_value)

    _label_rects(p2, true_positive + false_positive, ax)
    _label_rects(p4, true_negative + false_negative, ax)

    # legends
    plt.legend(
        (p1[0], p2[0], p3[0], p4[0]),
        ('Precision', 'False discovery rate', 'Negative predictive value',
         'False omission rate'), prop={'size': fontsize})

    legend_text = 'pre-fetch-size = %s\ndistance-to-fetch = %s\n' % (
        pre_fetch_size, distance_to_fetch)

    legend_text += 'cache-ratio = %s\ncommit count = %s' % (
        cache_ratio, REPO_DATA[repo_name]['commit_num'])

    text(
        0.025, 0.975, legend_text, ha='left', va='top', fontsize=fontsize,
        transform=ax.transAxes, multialignment='left',
        bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))

    fig.tight_layout()
    fig.subplots_adjust(left=0.04)
    plt.tick_params(labelsize=fontsize)

    # figure 2
    fig, ax = plt.subplots(figsize=figsize)
    # settings
    ax.set_xticks(ind + width)
    ax.set_xticklabels(counter)
    ax.set_ylim(0.0, y_lim)
    # plt.ylabel('ratio', fontsize=fontsize)
    plt.xlabel('10 bug-fixing commits after stopping FixCache at tHStart',
               fontsize=fontsize)
    plt.title("Accuracy and F1 score for %s.git" % (repo_name,),
              y=1.02, fontsize=fontsize)
    plt.grid(True)

    # showing the bars
    p5 = plt.bar(ind, accuracy, width, color='blue')
    p6 = plt.bar(ind + width, f1_score, width, color='orange')

    # legend
    plt.legend(
        (p5[0], p6[0]), ('Accuracy', 'F1 score'), prop={'size': fontsize})
    text(
        0.025, 0.975, legend_text, ha='left', va='top', fontsize=fontsize,
        transform=ax.transAxes, multialignment='left',
        bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.tight_layout()
    # figure 3
    fig.tight_layout()
    fig.subplots_adjust(left=0.04)
    plt.tick_params(labelsize=fontsize)

    # figure 3
    fig, ax = plt.subplots(figsize=figsize)
    # settings
    ax.set_xticks(ind + width)
    ax.set_xticklabels(counter)
    ax.set_ylim(0.0, y_lim)
    # plt.ylabel('ratio', fontsize=fontsize)
    plt.xlabel('10 bug-fixing commits after stopping FixCache at tHStart',
               fontsize=fontsize)
    plt.title("Recall and Specificity for %s.git" % (repo_name,),
              y=1.02, fontsize=fontsize)
    plt.grid(True)

    # showing the bars
    p7 = plt.bar(ind, sensitivity, width, color='#FF0081')
    p8 = plt.bar(ind + width, specificity, width, color='#7F0040')

    # legend
    plt.legend(
        (p7[0], p8[0]),
        ('Recall', 'Specificity'), prop={'size': fontsize})
    text(
        0.025, 0.975, legend_text, ha='left', va='top', fontsize=fontsize,
        transform=ax.transAxes, multialignment='left',
        bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))

    # showing all the figures
    fig.tight_layout()
    fig.subplots_adjust(left=0.04)
    plt.tick_params(labelsize=fontsize)
    plt.show()


def main(args):
    """Docstring."""
    fun = args.function
    if fun == 'plot_one':
        if args.v and args.dtf and args.pfs:
            plot_one(repo_name=args.repository, pre_fetch_size=args.pfs,
                     distance_to_fetch=args.dtf,
                     version='version_' + str(args.v))
        else:
            parser.error('--v, --dtf and --pfs have to be set')
    elif fun == 'plot_several':
        if args.v and args.dtf and args.pfs:
            plot_several(pre_fetch_size=args.pfs, distance_to_fetch=args.dtf,
                         version='version_' + str(args.v))
        else:
            parser.error('--v, --dtf and --pfs have to be set')
    elif fun == 'plot_fixed_cache_ratio':
        if args.v and args.cr:
            plot_fixed_cache_ratio(
                repo_name=args.repository, cache_ratio=args.cr,
                version='version_' + str(args.v))
        else:
            parser.error('--v and --cr have to be set')
    elif fun == 'plot_different_versions':
        if args.pfs and args.dtf:
            plot_different_versions(
                distance_to_fetch=args.dtf, repo_name=args.repository,
                pre_fetch_size=args.pfs)
        else:
            parser.error('--pfs and --dtf have to be set')
    elif fun == 'plot_speedup':
        if args.v and args.v2 and args.dtf and args.pfs:
            plot_speedup(
                repo_name=args.repository,
                distance_to_fetch=args.dtf,
                pre_fetch_size=args.pfs,
                versions=(
                    'version_' + str(args.v),
                    'version_' + str(args.v2)))
    elif fun == 'evaluation':
        if args.b and args.v and args.pfs and args.dtf and args.cr:
            evaluation(
                repo_name=args.repository, cache_ratio=args.cr,
                version='version_' + str(args.v), pre_fetch_size=args.pfs,
                distance_to_fetch=args.dtf, branch=args.b)
        else:
            parser.error('--b, --v, --pfs, --dtf and --cr are required')
    elif fun == 'evaluation_comparison':
        if args.b and args.v:
            evaluation_comparison(
                repo_name=args.repository, pre_fetch_size=args.pfs,
                version='version_' + str(args.v), branch=args.b)
    elif fun == 'plot_all':
        plot_all(version='version_' + str(args.v), repo_name=args.repository)

FUNCTION_CHOICES = [
    'plot_one',
    'plot_several',
    'plot_fixed_cache_ratio',
    'plot_different_versions',
    'plot_speedup',
    'evaluation',
    'plot_all',
    'evaluation_comparison'
]

parser = argparse.ArgumentParser(
    description='Show results of FixCache analysis')
parser.add_argument('-d', '-daemon', action='store_true')
parser.add_argument('function', metavar='fun', choices=FUNCTION_CHOICES)
parser.add_argument('repository', metavar='repo')
parser.add_argument('--cr', '--cache_ratio', type=float)
parser.add_argument('--pfs', '--pre_fetch_size', type=float)
parser.add_argument('--dtf', '--distance_to_fetch', type=float)
parser.add_argument('--v', '--version', type=int)
parser.add_argument('--v2', '--version2', type=int)
parser.add_argument('--b', '--branch', type=str, default='master')

if __name__ == "__main__":
    args = parser.parse_args()
    if args.function != 'plot_speedup' and args.v != CURRENT_VERSION:
        parser.error('Version has to be %s' % (CURRENT_VERSION,))

    if args.d:
        with daemon.DaemonContext():
            main(args)
    else:
        main(args)
