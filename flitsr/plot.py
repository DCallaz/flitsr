from matplotlib import pyplot as plt
from matplotlib import ticker as mtick
from typing import Dict, List
import re
import os
import sys
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser('plot', usage='Plot graphs of various results '
                            'generated by the merge script')
    parser.add_argument('-s', '--separate', action='store_true',
                        help='Plot separate graphs for each metric')
    parser.add_argument('-r', '--rel', action='store_true',
                        help='Plot graphs relative to the size of the SUTs '
                        'instead of using absolute numbers. This will plot '
                        'with the y-axis being a percentage.')
    parser.add_argument('-c', '--calcs', nargs='+', metavar='CALC',
                        help='Specify the list of calculations to include when '
                        'plotting. By default all available calculations are '
                        'included. NOTE: the names of the calculations need to '
                        'be found in the corresponding results files')
    parser.add_argument('-m', '--metrics', nargs='+', metavar='METRIC',
                        help='Specify the metrics to plot graphs for. By '
                        'default all metrics that appear in filenames of found '
                        'files will be plotted.')
    args = parser.parse_args()
    seperate = args.separate
    rel = args.rel
    custom = args.calcs
    metrics = args.metrics

    faults = []
    total = 0
    num_locs = 0
    if (os.path.isfile("size")):
        num_locs = int(open("size").readline())
    proj = os.getcwd().split("/")[-1].capitalize()
    for d in os.scandir():
        if (tcm and d.is_dir() and d.name.endswith("_Chart")):
            num = int(d.name.split('_')[0])
            faults.append(num)
        elif (d.is_dir() and d.name.endswith("-fault")):
            num = int(d.name.split('-')[0])
            faults.append(num)
    faults.sort()
    names: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    size = 0
    for f in faults:
        if (rel):
            if (tcm):
                file = open(str(f)+"-fault/results_rel")
            else:
                file = open(str(f)+"_fault_versions_Chart/results_rel")
        else:
            if (tcm):
                file = open(str(f)+"-fault/results")
            else:
                file = open(str(f)+"_fault_versions_Chart/results")
        line = file.readline()
        while (not line == ""):
            metric = line.strip()
            if (metric not in names):
                names[metric] = {}
            name = names[metric]
            line = file.readline()
            while (line.count("\t") == 1):
                mode = line.strip()
                if (mode not in name):
                    name[mode] = {}
                mod = name[mode]
                line = file.readline()
                while (line.count("\t") == 2):
                    calcs = line.strip().split(": ")
                    if (not calcs[0] in mod):
                        mod[calcs[0]] = []
                        size += 1
                    if (rel):
                        mod[calcs[0]].append(float(calcs[1][:-1]))
                    else:
                        mod[calcs[0]].append(float(calcs[1]))
                    line = file.readline()
    if (len(metrics) == 0):
        metrics = list(names.keys())
    color = ['r', 'b', 'g', 'y', 'm', 'c', 'k']
    shape = ['^', '.', 'v', '-']
    if (seperate):
        if (custom):
            size = len(custom)
        fig, axs = plt.subplots(size, len(metrics), sharey='row',
                                gridspec_kw={"left":   0.022,
                                             "bottom": 0.027,
                                             "right":  0.994,
                                             "top":    0.932,
                                             "wspace": 0.09,
                                             "hspace": 0.131})
        row = size
    else:
        fig, axs = plt.subplots(2, 2, sharey=True, sharex=True,
                                gridspec_kw={"left":   0.035,
                                             "bottom": 0.047,
                                             "right":  0.98,
                                             "top":    0.90,
                                             "wspace": 0.126,
                                             "hspace": 0.215})
        row = 2
    ax = 0

    for metric in metrics:
        modes = names[metric]
        for (i, mode) in enumerate(modes.keys()):
            calcs = modes[mode]
            if (not custom):
                custom = list(calcs.keys())
            for (j, calc) in enumerate(custom):
                values = calcs[calc]
                if (seperate):
                    axs[j, ax].plot(faults, values, str(color[i])+".-")
                    axs[j, ax].set_title(metric+" "+calc)
                    axs[j, ax].grid(True)
                    axs[j, ax].legend([x for x in list(modes.keys())],
                            prop={"size":12})
                else:
                    axs[int(ax/row), ax%row].plot(faults, values, str(color[i])+".-")
        if (not seperate):
            if (rel):
                axs[int(ax/row), ax%row].set_title("Comparison of the relative wasted"+
                    "effort for the first, average and med faults using the "+
                    metric+"\nmetric")
            else:
                axs[int(ax/row), ax%row].set_title("Comparison of the wasted"+
                    "effort for the first, average and med faults using the "+
                    metric+"\nmetric")
            axs[int(ax/row), ax%row].grid()
            axs[int(ax/row), ax%row].legend([x+" "+y for x in list(modes.keys())
                    for y in list(calcs.keys())], prop={"size":6})
        ax += 1

    if (rel):
        fmt = '%.0f%%' # Format you want the ticks, e.g. '40%'
        yticks = mtick.FormatStrFormatter(fmt)
        for a in axs:
            for ax in a:
                ax.yaxis.set_major_formatter(yticks)


    fig.suptitle(proj+" (size: "+str(num_locs)+")", fontsize=18)
    plt.show()
