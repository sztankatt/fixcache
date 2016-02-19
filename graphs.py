#! /usr/bin/env python
"""docstring."""
import csv
import os
import sys

import constants

from constants import REPO_DATA, version_color
from analysis import evaluate_repository
# from graph_data import plot_1_data

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from pylab import text


def _file_to_csv_by_name(version, repository_name, file_):
    """Get the csv file to a list of rows, as tuples."""
    dir_ = os.path.join(constants.CSV_ROOT, version, repository_name)
    file_ = os.path.join(
        dir_, file_
    )
    try:
        with open(file_, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            return [row for row in csv_reader]
    except:
        pass


def _file_to_csv(version, repository_name, pfs, dtf):
    """Read file into csv type python object."""
    file_ = ('analyse_by_cache_ratio_progressive_dtf_' + str(dtf) +
             '_pfs_' + str(pfs) + '.csv')

    return _file_to_csv_by_name(version, repository_name, file_)


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


def plot_several(pfs, dtf, version, figure_name=None):
    """Sample plot of several different repos."""
    x = range(100)
    legend = []

    fig, ax = plt.subplots()

    for repo_name in REPO_DATA:
        csv_reader = _file_to_csv(
            version,
            repo_name, pfs, dtf)
        y = get_column(csv_reader, 'hit_rate')
        if y is not None:
            plt.plot(x, y, color=REPO_DATA[repo_name]['color'])
            line = mlines.Line2D(
                [], [], color=REPO_DATA[repo_name]['color'],
                label=REPO_DATA[repo_name]['legend'], linewidth=2)
            legend.append(line)

    plt.legend(handles=legend, loc=4, fontsize=12)
    plt.ylabel('hit rate')
    plt.xlabel('cache size (%)')
    if figure_name is None:
        plt.title("FixCache for several repositories: %s" % (version,),
                  y=1.02)
    else:
        plt.title(figure_name)

    legend_text = 'pfs = %s, dtf = %s' % (
        pfs, dtf)
    text(0.978, 0.3, legend_text, ha='right', va='top',
         transform=ax.transAxes, multialignment='left', fontsize=12,
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def plot_one(repo_name, pfs, dtf, version, fig_name=None):
    """Plot a single repository data."""
    x = range(100)
    csv_reader = _file_to_csv(version, repo_name, pfs, dtf)

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader, 'hit_rate')
    pfs_size = get_column(csv_reader, 'pfs')
    dtf_size = get_column(csv_reader, 'dtf')

    fig = plt.figure()

    fig.suptitle(
        "Analysing fixcache for %s" % (repo_name + '.git',), fontsize=16,
        y=1.02)
    ax1 = plt.subplot(211)
    legend_text = 'pfs = %s, dtf = %s' % (
        pfs, dtf)
    text(0.55, 0.07, legend_text, ha='center', va='center',
         transform=ax1.transAxes, multialignment='left',
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    ax1.set_ylabel('hit rate')
    ax1.set_xlabel('cache size (%)')
    ax1.grid(True)
    ax1.plot(x, hit_rate, color='red', linewidth=2)

    ax2 = plt.subplot(212)
    ax2.plot(x, pfs_size, color="blue", linewidth=2)
    ax2.plot(x, dtf_size, color="green", linewidth=2)
    ax2.set_ylabel('discrete pfs/dtf sizes')
    ax2.set_xlabel('cache size (%)')
    ax2.grid(True)

    line1 = mlines.Line2D(
        [], [], color="blue",
        label="pfs size", linewidth=2)

    line2 = mlines.Line2D(
        [], [], color="green",
        label="dtf size", linewidth=2)

    ax2.legend(handles=[line1, line2], loc=2)

    plt.show()


def plot_fixed_cache_ratio(repo_name, cache_ratio, version, fig_name=None):
    """Fixed cache rate plot, variable pfs and dtf."""
    csv_reader = csv_reader = _file_to_csv_by_name(
        version,
        repo_name,
        'analyse_by_fixed_cache_%s.csv' % (cache_ratio,))

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader, 'hit_rate')
    # cache_size = get_column(csv_reader, 'cache_size')[0]

    base = [float(x + 2) / 20 for x in range(10)]

    dtf_size = 6 * base
    pfs_size = []
    for i in base[:6]:
        pfs_size = pfs_size + 10 * [i]
    print len(pfs_size), len(dtf_size)

    sc = plt.scatter(pfs_size, dtf_size, s=80,
                     color=[str(x) for x in hit_rate],
                     cmap=plt.cm.viridis)

    plt.title(
        'dtf and pfs analysis for %s.git: %s' % (repo_name, version))

    plt.ylabel('dtf (% of cache size)')
    plt.xlabel('pfs (% of cache size)')

    fig = plt.gcf()
    axcb = fig.colorbar(sc)
    axcb.set_label('Hit rate')

    plt.show()


def plot_different_versions(repo_name, pfs, dtf, fig_name=None):
    """Sample plot of several different repos."""
    x = range(100)
    legend = []

    fig, ax = plt.subplots()

    for version in version_color:
        csv_reader = _file_to_csv(
            version,
            repo_name, pfs, dtf)
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
        pfs, dtf, REPO_DATA[repo_name]['commit_num'])
    text(0.55, 0.07, legend_text, ha='center', va='center',
         transform=ax.transAxes, multialignment='left',
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def plot_speedup(repo_name, pfs, dtf, *versions):
    """Speedup plot."""
    x = range(100)
    if len(versions) != 2:
        return
    csv_reader1 = _file_to_csv(
        versions[0], repo_name,
        pfs, dtf)
    y1 = get_column(csv_reader1, 'ttr')

    csv_reader2 = _file_to_csv(
        versions[1], repo_name,
        pfs, dtf)

    y2 = get_column(csv_reader2, 'ttr')

    fig, ax = plt.subplots()

    if y1 is not None and y2 is not None:
        speedup_y = [float(y1[i]) / float(y2[i]) for i in x]

        plt.plot(x, speedup_y, color='blue')

    plt.title('Speedup of %s.git from %s to %s' % (
        repo_name, versions[0], versions[1]),
        y=1.02)
    plt.ylabel('speedup')
    plt.xlabel('cache size (%)')
    legend_text = 'pfs = %s, dtf = %s\ncommit_num = %s' % (
        pfs, dtf, REPO_DATA[repo_name]['commit_num'])
    text(0.98, 0.03, legend_text, ha='right', va='bottom',
         transform=ax.transAxes, multialignment='left',
         bbox=dict(alpha=1.0, boxstyle='square', facecolor='white'))
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def evaluation(repo_name, cache_ratio, pfs,
               dtf, version, branch='master', **kwargs):
    """Evaluate a repository, produce an evaluation graph."""
    if evaluate_repository(repo_name, float(cache_ratio), float(pfs),
                           float(dtf), version, branch=branch, **kwargs):
        metadata = _file_to_csv_by_name(
            version, repo_name,
            'evaluate_%s_cr_%s_pfs_%s_dtf_%s_metadata.csv' % (
                repo_name, cache_ratio, pfs, dtf))[0]

        csv_reader = _file_to_csv_by_name(
            version, repo_name,
            'evaluate_%s_cr_%s_pfs_%s_dtf_%s.csv' % (
                repo_name, cache_ratio, pfs, dtf))

        x = get_column(csv_reader, 'counter')
        true_positive = get_column(csv_reader, 'true_positive')
        false_positive = get_column(csv_reader, 'false_positive')
        true_negative = get_column(csv_reader, 'true_negative')
        false_negative = get_column(csv_reader, 'false_negative')

        true_positive = [int(i) for i in true_positive]
        false_positive = [int(i) for i in false_positive]
        true_negative = [int(i) for i in true_negative]
        false_negative = [int(i) for i in false_negative]
        fig, ax = plt.subplots()

        if x is not None:
            if true_positive is not None:
                plt.plot(x, true_positive, color='blue')

            if false_positive is not None:
                plt.plot(x, false_positive, color='red')

            if true_negative is not None:
                plt.plot(x, true_negative, color='orange')

            if false_negative is not None:
                plt.plot(x, false_negative, color='green')

            ymax = max([max(true_positive), max(false_negative),
                        max(true_negative), max(false_positive)])
            print ymax
            ax.set_ylim(-0.5, float(ymax) * 1.1)
        plt.grid(True)
        plt.show()


def main(function, *args):
    """Docstring."""
    functions = {
        'plot_one': plot_one,
        'plot_several': plot_several,
        'plot_fixed_cache_ratio': plot_fixed_cache_ratio,
        'plot_different_versions': plot_different_versions,
        'plot_speedup': plot_speedup,
        'evaluation': evaluation

    }

    functions[function](*args)

if __name__ == "__main__":
    main(*sys.argv[1:])
