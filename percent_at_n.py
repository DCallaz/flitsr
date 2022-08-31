from weffort import getTie
import math
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import sys
import copy
import ast
from enum import Enum
import numpy as np

def getBumps(faults, ranking, groups, worst_effort=False, collapse=False):
    if (len(faults) == 0):
        return [0.0]
    faults = copy.deepcopy(faults) # needed to remove groups of fault locations
    i = 0
    total = 0
    size = 0
    bumps = []
    if (collapse):
        size = len(groups)
    else:
        for group in groups:
            size += len(group)
    while (i < len(ranking)):
        uuts,group_len,curr_faults,curr_fault_groups,i = getTie(i, faults,
                ranking, groups, worst_effort)
        if (collapse):
            for f in range(curr_fault_groups):
                expect_value = (group_len+1)/(curr_fault_groups+1) # - 1
                bumps.append((total+(f+1)*expect_value)/size)
            total += group_len
        else:
            for f in range(curr_faults):
                expect_value = (len(uuts)+1)/(curr_faults+1) # - 1
                bumps.append((total+(f+1)*expect_value)/size)
            total += len(uuts)
    return bumps

def combine(results):
    size = len(results)
    total = 0
    pointers = [0]*size
    final = [len(r) for r in results]
    combined = []
    while (pointers != final):
        curr = [(math.inf if (pointers[i] == len(results[i])) else results[i][pointers[i]])
                for i in range(size)]
        min_ = min(curr)
        indexes = [i for i,x in enumerate(curr) if x == min_]
        for i in indexes:
            pointers[i] += 1
            total += 100/(len(results[i])*size)
        combined.append((min_, round(total, 8)))
    return combined

plot_type = Enum("plot_type", "metric mode")

def read_comb_file(comb_file):
    lines = open(comb_file).readlines()
    metrics = []
    modes = []
    metric = None
    mode = None
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

def plot(plot_file, log=True, all=False, type=plot_type.metric, metrics=None):
    modes = []
    comb_points = {}
    if (metrics == None):
        metrics,modes,comb_points = read_comb_file(plot_file)
    else:
        _,modes,comb_points = read_comb_file(plot_file)
    points = {}
    for item in comb_points.items():
        key = item[0]
        x = [0]
        y = [0]
        for inc in item[1]:
            x.append(inc[0])
            y.append(inc[1])
        #x.append(100)
        #y.append(100)
        points[key] = (x, y)
    split = metrics
    merged = modes
    if (type == plot_type.mode):
        split = modes
        merged = metrics
    fig, axs = plt.subplots(1,1 if all else len(split),
                gridspec_kw={"left": 0.024,
                 "bottom": 0.038,
                 "right":0.99,
                 "top": 0.978,
                 "wspace": 0.2,
                 "hspace": 0.2})
    color = list(cm.rainbow(np.linspace(0, 1, len(split))))
    style = ["-", "--", ":"]
    marker = ['v', 'o', '+', '8', 's', 'p', '*', '^', 'x', 'D', '<', '>']
    i = 0
    labels = []
    for s in split:
        j = 0
        for m in merged:
            if (m == "Base metric" or s == "Harmonic" or s == "Ochiai"
                    or s == "Tarantula"):
                if (type == plot_type.mode):
                    point = points[(m, s)]
                else:
                    point = points[(s, m)]
                if (all):
                    labels.append(s + " " + (m if m != "Base metric" else ""))
                    axs.plot(point[0], point[1], style[j], color=color[i],
                            marker=marker[i], markevery=0.1)
                else:
                    axs[i].plot(point[0], point[1])
            j += 1
        i += 1
    #plt.step(x,y)
    for i in range(1 if (all) else len(axs)):
        if (all):
            ax = axs
        else:
            ax = axs[i]
        if (all):
            ax.legend(labels)
            #ax.set_title("")
        else:
            ax.legend(merged)
            ax.set_title(split[i])
        if (log):
            ax.set_xscale("log")
            ax.set_xticks([0.01, 0.1, 1, 10, 100])
        #plt.ylim(0, 100)
        #plt.xlim(0, 100)
        ax.grid()
    plt.show()

def auc_calc(points, cut_off):
    auc = 0
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
            metrics = None
            log = True
            all = False
            i = 3
            while (True):
                if (len(sys.argv) > i):
                    if (sys.argv[i] == "mode"):
                        split = plot_type.mode
                    elif (sys.argv[i].startswith("[")):
                        metrics = [x.strip() for x in
                                sys.argv[i][1:-1].split(",")]
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
            plot(plot_file, log=log, all=all, type=split, metrics=metrics)
        elif (mode == "auc"):
            comb_file = sys.argv[2]
            metrics,modes,points = read_comb_file(comb_file)
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
