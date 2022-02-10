from tcm_input import read_table
from matplotlib import pyplot as plt
import re
import os
import sys

if __name__ == "__main__":
    seperate = False
    if (len(sys.argv) > 1 and sys.argv[1] == "sep"):
        seperate = True
    faults = []
    total = 0
    table,num_locs,num_tests,details = read_table("reference.txt")
    for d in os.scandir():
        if (d.is_dir()):
            num = int(d.name.split('-')[0])
            faults.append(num)
    faults.sort()
    names = {}
    for f in faults:
        file = open(str(f)+"-fault/results")
        line = file.readline()
        while (not line == ""):
            metric = line.strip()
            if (not metric in names):
                names[metric] = {}
            name = names[metric]
            line = file.readline()
            while (line.count("\t") == 1):
                mode = line.strip()
                if (not mode in name):
                    name[mode] = {}
                mod = name[mode]
                line = file.readline()
                while (line.count("\t") == 2):
                    calc = line.strip().split(": ")
                    if (not calc[0] in mod):
                        mod[calc[0]] = []
                    mod[calc[0]].append(float(calc[1]))
                    line = file.readline()
    color = ['r', 'b', 'g', 'y']
    shape = ['^', '.', 'v']
    if (seperate):
        fig, axs = plt.subplots(3,4, sharey='row',
                gridspec_kw={"left": 0.028,
                 "bottom": 0.05,
                 "right":0.981,
                 "top": 0.93,
                 "wspace": 0.2,
                 "hspace": 0.316})
        row = 3
    else:
        fig, axs = plt.subplots(2,2, sharey=True, sharex=True,
                gridspec_kw={"left": 0.035,
                 "bottom": 0.047,
                 "right":0.98,
                 "top": 0.924,
                 "wspace": 0.126,
                 "hspace": 0.215})
        row = 2
    ax = 0
    for metric in names.keys():
        #print(metric)
        modes = names[metric]
        i = 0
        for mode in modes.keys():
            #print(mode)
            calcs = modes[mode]
            j = 0
            for calc in calcs.keys():
                values = calcs[calc]
                #print(faults, values)
                if (seperate):
                    axs[j, ax].plot(faults, values, str(color[i])+str(shape[j])+"-")
                    axs[j, ax].set_title("Comparison of the wasted effort for the "+calc
                            +"\nfault using the "+metric+" metric (project size:"+
                            str(num_locs)+")")
                    axs[j, ax].grid(True)
                    axs[j, ax].legend([x for x in list(modes.keys())],
                            prop={"size":10})
                else:
                    axs[int(ax/row), ax%row].plot(faults, values, str(color[i])+str(shape[j])+"-")
                j += 1
            i += 1
        if (not seperate):
            axs[int(ax/row), ax%row].set_title("Comparison of the wasted effort for the first, average and"+
                    " last faults using the "+metric+"\nmetric (project size:"+
                    str(num_locs)+")")
            axs[int(ax/row), ax%row].grid()
            axs[int(ax/row), ax%row].legend([x+" "+y for x in list(modes.keys())
                    for y in list(calcs.keys())], prop={"size":6})
        ax += 1
    plt.show()
