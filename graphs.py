#! /usr/bin/env python
"""docstring."""
import csv
import os
import sys

import constants

from graph_data import graph_data
# from graph_data import plot_1_data

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def file_to_csv_by_name(version, repository_name, file_):
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


def file_to_csv(version, repository_name, pfs, dtf):
    """Read file into csv type python object."""
    file_ = ('analyse_by_cache_ratio_progressive_dtf_' + str(dtf) +
             '_pfs_' + str(pfs) + '.csv')

    return file_to_csv_by_name(version, repository_name, file_)


def calc_hit_rate(x, y):
    """Calculate hit rate based on hit and miss value."""
    lookups = int(x) + int(y)
    print x, y, lookups
    hit_rate = float(x) / float(lookups)
    return hit_rate


def get_column(csv_reader, col_name):
    """Get column."""
    if csv_reader is not None:
        if col_name == 'hit_rate':
            return [calc_hit_rate(x['hits'], x['misses']) for x in csv_reader]
        else:
            return [x[col_name] for x in csv_reader]


def plot_several(version, pfs, dtf, figure_name=None):
    """Sample plot of several different repos."""
    x = range(100)
    legend = []
    for curve in graph_data['curves']:
        csv_reader = file_to_csv(
            version,
            curve['options']['repo'], pfs, dtf)
        y = get_column(csv_reader, 'hit_rate')
        if y is not None:
            plt.plot(x, y, color=curve['options']['color'])
            line = mlines.Line2D(
                [], [], color=curve['options']['color'],
                label=curve['args'][0], linewidth=2)
            legend.append(line)

    plt.legend(handles=legend, loc=4)
    plt.ylabel('hit rate')
    plt.xlabel('cache size (%)')
    if figure_name is None:
        plt.title("Fixcache for several repositories")
    else:
        plt.title(figure_name)
    plt.text(2, 0.95, 'pfs=%s, dtf=%s' % (pfs, dtf))
    plt.grid(True)
    plt.autoscale(False)
    plt.show()


def plot_one(version, repo_name, pfs, dtf, fig_name=None):
    """Plot a single repository data."""
    x = range(100)
    csv_reader = file_to_csv(version, repo_name, pfs, dtf)

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader, 'hit_rate')
    pfs_size = get_column(csv_reader, 'pfs')
    dtf_size = get_column(csv_reader, 'dtf')

    fig = plt.figure()

    fig.suptitle(
        "Analysing fixcache for %s" % (repo_name + '.git',), fontsize=16)
    ax1 = plt.subplot(211)
    ax1.text(2, 0.8, 'pfs=%s, dtf=%s' % (pfs, dtf))
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


def plot_fixed_cache_rate(version, repo_name, cache_ratio, fig_name=None):
    csv_reader = csv_reader = file_to_csv_by_name(
        version,
        repo_name,
        'analyse_by_fixed_cache_%s.csv' % (cache_ratio,))

    if csv_reader is None:
        return

    hit_rate = get_column(csv_reader, 'hit_rate')
    cache_size = get_column(csv_reader, 'cache_size')[0]
    pfs_size = [
        float(x) * 100 / int(cache_size) for x in get_column(csv_reader, 'pfs')
    ]
    dtf_size = [
        float(x) * 100 / int(cache_size) for x in get_column(csv_reader, 'dtf')
    ]
    # pfs_size = get_column(csv_reader, 'pfs')
    # dtf_size = get_column(csv_reader, 'dtf')
    sc = plt.scatter(pfs_size, dtf_size, s=80,
                     color=[str(x) for x in hit_rate],
                     cmap=plt.cm.viridis)

    print hit_rate

    plt.title(
        'dtf and pfs for %s.git with cahe_ratio=%s' % (repo_name, cache_ratio))

    plt.ylabel('dtf (% of cache size)')
    plt.xlabel('pfs (% of cache size)')

    fig = plt.gcf()
    axcb = fig.colorbar(sc)
    axcb.set_label('Hit rate')

    plt.show()


def main(function, *args):
    """Docstring."""
    functions = {
        'plot_one': plot_one,
        'plot_several': plot_several,
        'plot_fixed_cache_rate': plot_fixed_cache_rate
    }

    functions[function](*args)

if __name__ == "__main__":
    main(*sys.argv[1:])
