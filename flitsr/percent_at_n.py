import math
import sys
import copy
import ast
import numpy as np
from enum import Enum
from typing import Dict, List, Tuple, Optional
from flitsr.spectrum import Spectrum
from flitsr.tie import Ties


def getBumps(ties: Ties, spectrum: Spectrum, worst_effort=False,
             collapse=False) -> List[float]:
    if (len(ties.faults) == 0):
        return [0.0]
    tie_iter = iter(ties)
    total = 0
    size = 0
    if (collapse):
        size = len(spectrum.groups)
    else:
        for group in spectrum.groups:
            size += len(group)
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
    import matplotlib.cm as cm  # type: ignore
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
    split = metrics
    merged = modes
    if (type == plot_type.mode):
        split = modes
        merged = metrics
    plt.rcParams.update({'font.size': 10})
    fig, axs = plt.subplots(1, 1 if all else len(split),
                            gridspec_kw={"left": 0.045,
                                         "bottom": 0.06,
                                         "right": 0.99,
                                         "top": 0.99,
                                         "wspace": 0.2,
                                         "hspace": 0.2} if all else {})
    color = list(cm.rainbow(np.linspace(0, 1, len(split))))
    style = [(), (6, 3), (1, 3), (1, 3, 6, 3), (3, 3), (6, 3, 3, 3)]
    marker = ['D', 'o', '^', '8', 's', 'p', '*', 'x', '+', 'v', '<', '>', 'P',
              'h', 'X', 'H', 'd', '|', '_']
    lines = []
    for (i, s) in enumerate(split):
        for (j, m) in enumerate(merged):
            if (m == "Base" or flitsrs is None or s in flitsrs):
                if (type == plot_type.mode):
                    point = points[(m, s)]
                else:
                    point = points[(s, m)]
                # print(point)
                if (all):
                    ls = axs.plot(point[0], point[1], dashes=style[j],
                             color=color[i], marker=marker[i], markevery=0.1)
                    if (m == "Base"):
                        lines.append(ls[0])
                else:
                    axs[i].plot(point[0], point[1])
    # plt.step(x,y)
    for i in range(1 if (all) else len(axs)):
        if (all):
            ax = axs
        else:
            ax = axs[i]
        if (all):
            # lines = ax.get_lines()[::len(modes)]
            dummy_lines = []
            for j in range(len(merged)):
                dummy_lines.append(ax.plot([], [], c="black",
                                           dashes=style[j])[0])
            t_dummy, = ax.plot([], [], marker='None', ls='None')
            labels = [r'$\mathbf{Metrics\!:}$'] + metrics + \
                     [r'$\mathbf{Types\!:}$'] + modes
            all_lines = [t_dummy] + lines + [t_dummy] + dummy_lines
            ax.legend(all_lines, labels)
            # ax.set_title("")
        else:
            ax.legend(merged)
            ax.set_title(split[i])
        if (log):
            ax.set_xscale("log")
            ax.set_xticks([0.01, 0.1, 1, 10, 100], [0.01, 0.1, 1, 10, 100])
        # plt.ylim(0, 100)
        # plt.xlim(0, 100)
        ax.grid()
    plt.show()


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


if __name__ == "__main__":
    if (len(sys.argv) > 1):
        mode = sys.argv[1]
        if (mode == "combine"):
            infile = sys.argv[2]
            lines = open(infile).readlines()
        elif (mode == "plot"):
            plot_file = sys.argv[2]
            split = plot_type.metric
            metrics: Optional[List[str]] = None
            flitsrs = None
            log = True
            all = False
            i = 3
            while (True):
                if (len(sys.argv) > i):
                    if (sys.argv[i] == "mode"):
                        split = plot_type.mode
                    elif (sys.argv[i].startswith("metrics=[")):
                        metrics = [x.strip() for x in
                                   sys.argv[i][9:-1].split(",")]
                    elif (sys.argv[i].startswith("flitsrs=[")):
                        flitsrs = [x.strip() for x in
                                   sys.argv[i][9:-1].split(",")]
                    elif (sys.argv[i] == "linear"):
                        log = False
                    elif (sys.argv[i] == "log"):
                        log = True
                    elif (sys.argv[i] == "all"):
                        all = True
                    else:
                        print("Unknown option:", sys.argv[i])
                        exit(1)
                    i += 1
                else:
                    break
            plot(plot_file, log=log, all=all, type=split, metrics=metrics,
                 flitsrs=flitsrs)
        elif (mode == "auc"):
            comb_file = sys.argv[2]
            metrics, modes, points = read_comb_file(comb_file)
            cutoff = 101.0
            i = 3
            while (True):
                if (len(sys.argv) > i):
                    if (sys.argv[i].startswith("[")):
                        metrics = [x.strip() for x in
                                   sys.argv[i][1:-1].split(",")]
                    elif (sys.argv[i].startswith("cutoff=")):
                        cutoff = float(sys.argv[i].split("=")[1])
                    else:
                        print("Unknown option:", sys.argv[i])
                        exit(1)
                    i += 1
                else:
                    break
            for metric in metrics:
                base = auc_calc(points[(metric, "Base metric")], cutoff)
                flitsr = auc_calc(points[(metric, "FLITSR")], cutoff)
                flitsr_m = auc_calc(points[(metric, "FLITSR*")], cutoff)
                print("{} FLITSR imprv: {:.6%}".format(metric, flitsr/base))
                print("{} FLITSR* imprv: {:.6%}".format(metric, flitsr_m/base))
