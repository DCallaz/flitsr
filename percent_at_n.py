from weffort import getTie
import math
from matplotlib import pyplot as plt
import sys
import copy
import ast

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

def plot(plot_file):
    lines = plot_file.readlines()
    metrics = []
    modes = []
    i = 0
    j = 0
    labels = []
    fig, axs = plt.subplots(1,12)
    for line in lines:
        if (line.startswith("\t\t")):
            comb = ast.literal_eval(line.strip().split(": ")[1])
            x = [0]
            y = [0]
            for inc in comb:
                x.append(inc[0])
                y.append(inc[1])
            x.append(100)
            y.append(100)
            axs[i].plot(x, y)
        elif (line.startswith("\t")):
            mode = line.strip()
            if (mode not in modes):
                j = len(modes)
                modes.append(mode)
            else:
                j = modes.index(mode)
        else:
            metric = line.strip()
            if (metric not in metrics):
                i = len(metrics)
                metrics.append(metric)
            else:
                i = metrics.index(metric)
    #plt.step(x,y)
    for i in range(len(axs)):
        ax = axs[i]
        ax.set_xticks([0.01, 0.1, 1, 10, 100])
        ax.legend(modes)
        ax.set_xscale("log")
        ax.set_title(metrics[i])
        #plt.ylim(0, 100)
        #plt.xlim(0, 100)
        ax.grid()
    plt.show()

def auc_calc(points):
    auc = 0
    for i in range(1, len(points)):
        auc += (points[i][0] - points[i-1][0]) * points[i-1][1]
    return auc

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        mode = sys.argv[1]
        if (mode == "combine"):
            infile = sys.argv[2]
            lines = open(infile).readlines()
        elif (mode == "plot"):
            plot_file = open(sys.argv[2])
            plot(plot_file)
