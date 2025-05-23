# PYTHON_ARGCOMPLETE_OK
import math
import sys
import ast
import numpy as np
from argparse import ArgumentParser
import argcomplete
from enum import Enum
from typing import Dict, List, Tuple, Optional
from flitsr.spectrum import Spectrum
from flitsr.tie import Ties
from flitsr.suspicious import Suspicious


def getBumps(ties: Ties, spectrum: Spectrum, worst_effort=False,
             collapse=False) -> List[float]:
    if (len(ties.faults) == 0):
        return [0.0]
    tie_iter = iter(ties)
    total = 0
    size = 0
    if (collapse):
        size = len(spectrum.groups())
    else:
        for group in spectrum.groups():
            size += len(group.get_elements())
    bumps = [float(size)]
    try:
        while (True):
            tie = next(tie_iter)
            for f in range(1, tie.num_faults()+1):
                expect_value = tie.expected_value(f, False, collapse)
                bumps.append(total+expect_value)
            total += tie.len(collapse)
    except StopIteration:
        pass
    return bumps


def combine(results: List[Tuple[float, List[float]]]) -> List[Tuple[float, float]]:
    def err(x):
        return max(10**-6, (math.log((99*x/100) + 1)/math.log(100))*0.1)
    size = len(results)
    total = 0.0
    pointers = [0]*size
    final = [len(r[1]) for r in results]
    combined = []
    def val(results, pointer, i):
        if (pointer < len(results[i][1])):
            return results[i][1][pointer]*100/results[i][0]
    while (pointers != final):
        # get the minimum next value
        min_ = min([v for v in (val(results, pointers[i], i) for i in range(size))
                        if v is not None])
        indexes = []
        for i in range(size):
            j = 0
            while ((v := val(results, pointers[i]+j, i)) is not None):
                if (abs(min_ - v) < err(min_)):
                    j += 1
                else:
                    break
            if (j > 0):
                indexes.append((i, j))
        #curr = [(math.inf if (pointers[i] == len(results[i])) else results[i][pointers[i]])
                #for i in range(size)]
        #min_ = min(curr)
        #indexes = [i for i,x in enumerate(curr) if x - min_ < 10e-4]
        for (i, j) in indexes:
            pointers[i] += j
            total += j * (100/(len(results[i][1])*size))
        combined.append((min_, round(total, 8)))
    return combined


plot_type = Enum("plot_type", "metric mode")


def read_comb_file(comb_file: str) -> Tuple[List[str], List[str],
        Dict[Tuple[str, str], List[Tuple[float, float]]]]:
    lines = open(comb_file).readlines()
    metrics = []
    modes = []
    metric = ""
    mode = ""
    points = {}
    for line in lines:
        if (line.startswith("\t\t")):
            comb = ast.literal_eval(line.strip().split(": ")[1])
            comb.append((100.0, 100.0))
            points[(metric, mode)] = comb
        elif (line.startswith("\t")):
            mode = line.strip()
            if (mode not in modes):
                modes.append(mode)
        else:
            metric = line.strip()
            if (metric not in metrics):
                metrics.append(metric)
    return metrics, modes, points


def plot(plot_file: str, log=True, all=False, type=plot_type.metric,
         metrics=None, flitsrs=None):
    from matplotlib import pyplot as plt
    modes: List[str] = []
    comb_points: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}
    if (metrics is None):
        metrics, modes, comb_points = read_comb_file(plot_file)
    else:
        _, modes, comb_points = read_comb_file(plot_file)
    points = {}
    for item in comb_points.items():
        key = item[0]
        x = [0.0]
        y = [0.0]
        for inc in item[1]:
            x.append(inc[0])
            y.append(inc[1])
        points[key] = (x, y)
    if (all):
        num_plots = 1
    elif (type == plot_type.metric):
        num_plots = len(metrics)
    else:
        num_plots = len(modes)
    plt.rcParams.update({'font.size': 10})
    fig, axs = plt.subplots(1, num_plots,
                            gridspec_kw={"left": 0.045,
                                         "bottom": 0.06,
                                         "right": 0.99,
                                         "top": 0.99,
                                         "wspace": 0.2,
                                         "hspace": 0.2} if all else {})
    if (all):
        plot_all(axs, points, metrics, modes, flitsrs, log)
    else:
        plot_sep(axs, points, type, metrics, modes, log)
    plt.show()


def plot_all(axs, points, metrics, modes, flitsrs, log):
    import matplotlib.cm as cm
    color = list(cm.rainbow(np.linspace(0, 1, len(metrics))))
    style = [(), (6, 3), (1, 3), (1, 3, 6, 3), (3, 3), (6, 3, 3, 3)]
    marker = ['D', 'o', '^', '8', 's', 'p', '*', 'x', '+', 'v', '<', '>', 'P',
              'h', 'X', 'H', 'd', '|', '_']
    lines = []
    for (i, me) in enumerate(metrics):
        for (j, mo) in enumerate(modes):
            if ((me, mo) in points and (mo == "Base" or flitsrs is None
                                        or me in flitsrs)):
                point = points[(me, mo)]
                # print(point)
                ls = axs.plot(point[0], point[1], dashes=style[j],
                              color=color[i], marker=marker[i], markevery=0.1)
                if (mo == "Base"):
                    lines.append(ls[0])
    # lines = axs.get_lines()[::len(modes)]
    dummy_lines = []
    for j in range(len(modes)):
        dummy_lines.append(axs.plot([], [], c="black",
                                    dashes=style[j])[0])
    t_dummy, = axs.plot([], [], marker='None', ls='None')
    labels = [r'$\mathbf{Metrics\!:}$'] + metrics + \
             [r'$\mathbf{Types\!:}$'] + modes
    all_lines = [t_dummy] + lines + [t_dummy] + dummy_lines
    axs.legend(all_lines, labels)
    # axs.set_title("")
    plot_log(axs, log)
    # plt.ylim(0, 100)
    # plt.xlim(0, 100)
    axs.grid()


def plot_sep(axs, points, type, metrics, modes, log):
    if (type == plot_type.metric):
        split, merged = metrics, modes
    else:
        split, merged = modes, metrics
    for (i, s) in enumerate(split):
        for (j, m) in enumerate(merged):
            if (type == plot_type.mode and (m, s) in points):
                point = points[(m, s)]
            elif ((s, m) in points):
                point = points[(s, m)]
            # print(point)
            axs[i].plot(point[0], point[1])
    # plt.step(x,y)
    for i in range(len(axs)):
        ax = axs[i]
        ax.legend(merged)
        ax.set_title(split[i])
        plot_log(ax, log)
        # plt.ylim(0, 100)
        # plt.xlim(0, 100)
        ax.grid()


def plot_log(ax, log):
    if (log):
        ax.set_xscale("log")
        ax.set_xticks([0.01, 0.1, 1, 10, 100], [0.01, 0.1, 1, 10, 100])


def auc_calc(points: List[Tuple[float, float]],
             cut_off=101.0) -> float:
    points = sorted(points, key=lambda x: x[0])  # sort points, sanity check
    auc = 0.0
    if (len(points) == 0 or points[-1][0] != 100.0):
        points.append((100.0, 100.0))
    for i in range(1, len(points)):
        if (points[i][0] >= cut_off):
            break
        auc += (points[i][0] - points[i-1][0]) * points[i-1][1]
    return auc


def main(argv: Optional[List[str]] = None):
    parser = ArgumentParser(prog="percent_at_n")
    subparsers = parser.add_subparsers(title='Modes', description='The '
                                       'following modes are available '
                                       'for the percent_at_n command:',
                                       required=True, dest='mode')
    combine_parser = subparsers.add_parser('combine')
    combine_parser.add_argument('input_file')

    met_names = list(map(str.capitalize, Suspicious.getNames(True)))
    plot_parser = subparsers.add_parser('plot', help='Plots the percentage at '
                                        'n graph for the given input file '
                                        'produced by the merge script')
    plot_parser.add_argument('plot_file', help='The input file generated by '
                             'the FLITSR merge script')
    plot_parser.add_argument('-a', '--all', action='store_true',
                             help='Plots one graph containing all metrics and '
                             'advanced types. You may optionally filter the '
                             'metrics that are plotted and for which metrics '
                             'advanced types are plotted for by the --metrics '
                             'and --types options')
    plot_parser.add_argument('-m', '--metrics', nargs='+', choices=met_names,
                             help='Specifies the metrics to plot for the --all '
                             'plotting style. Allowed values are: '
                             f'[{", ".join(met_names)}]', metavar='METRIC')
    plot_parser.add_argument('-t', '--types', nargs='+', choices=met_names,
                             help='Specifies the metrics for which to plot '
                             'advanced types for using the --all plotting '
                             'style. See --metrics for allowed values',
                             metavar='METRIC')
    plot_parser.add_argument('-s', '--split-type', choices=['metric', 'type'],
                             help='Determines whether to plot separate graphs '
                             'for each metric, or for each type',
                             default='metric')
    plot_parser.add_argument('-l', '--log', action='store_true',
                             help='By default graphs are plot with both axes '
                             'in linear scale. This option enables plotting '
                             'the x-axis in log scale instead')

    auc_parser = subparsers.add_parser('auc', help='Calculates the Area Under '
                                       'Curve (AUC) for each metric and '
                                       'advanced type in the given input file '
                                       'generated by the merge script')
    auc_parser.add_argument('comb_file', help='The input file generated by '
                            'the FLITSR merge script')
    auc_parser.add_argument('-m', '--metrics', nargs='+', choices=met_names,
                            help='Specifies the subset of metrics to '
                            'calculate AUC values for. Allowed values are: '
                            f'[{", ".join(met_names)}]', metavar='METRIC')
    auc_parser.add_argument('-c', '--cutoff', action='store', type=float,
                            help='Specifies the percentage cut-off point to '
                            'use for the AUC calculations', default='101.0')
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    if (args.mode == "combine"):
        infile = args.input_file
        lines = open(infile).readlines()
    elif (args.mode == "plot"):
        plot(args.plot_file, log=args.log, all=args.all, type=args.split_type,
             metrics=args.metrics, flitsrs=args.types)
    elif (args.mode == "auc"):
        comb_file = args.comb_file
        metrics, modes, points = read_comb_file(comb_file)
        cutoff = args.cutoff
        if (args.metrics):
            metrics = args.metrics
        for metric in metrics:
            base = auc_calc(points[(metric, "Base metric")], cutoff)
            flitsr = auc_calc(points[(metric, "FLITSR")], cutoff)
            flitsr_m = auc_calc(points[(metric, "FLITSR*")], cutoff)
            print("{} FLITSR imprv: {:.6%}".format(metric, flitsr/base))
            print("{} FLITSR* imprv: {:.6%}".format(metric, flitsr_m/base))


if __name__ == "__main__":
    main()
