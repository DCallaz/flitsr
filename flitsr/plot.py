from matplotlib import pyplot as plt # type: ignore
from matplotlib import ticker as mtick
import re
import os
import sys

if __name__ == "__main__":
    seperate = False
    rel = False
    tcm = True
    custom = None
    metrics = []
    i = 1
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "sep"):
                seperate = True
            elif (sys.argv[i] == "rel"):
                rel = True
            elif (sys.argv[i] == "tcm"):
                tcm = True
            elif (sys.argv[i].startswith("calcs=[")):
                index = sys.argv[i].index("[")+1
                custom = [x.strip() for x in sys.argv[i][index:-1].split(",")]
            elif (sys.argv[i].startswith("metrics=[")):
                index = sys.argv[i].index("[")+1
                metrics = [x.strip() for x in sys.argv[i][index:-1].split(",")]
            else:
                print("Unknown option:", sys.argv[i])
                exit(1)
            i += 1
        else:
            break
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
    names = {}
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
                        size += 1
                    if (rel):
                        mod[calc[0]].append(float(calc[1][:-1]))
                    else:
                        mod[calc[0]].append(float(calc[1]))
                    line = file.readline()
    if (len(metrics) == 0):
        metrics = names.keys()
    color = ['r', 'b', 'g', 'y', 'm', 'c', 'k']
    shape = ['^', '.', 'v', '-']
    if (seperate):
        if (custom):
            size = len(custom)
        fig, axs = plt.subplots(size,len(metrics), sharey='row',
                gridspec_kw={"left": 0.022,
                 "bottom": 0.027,
                 "right":0.994,
                 "top": 0.932,
                 "wspace": 0.09,
                 "hspace": 0.131})
        row = size
    else:
        fig, axs = plt.subplots(2,2, sharey=True, sharex=True,
                gridspec_kw={"left": 0.035,
                 "bottom": 0.047,
                 "right":0.98,
                 "top": 0.90,
                 "wspace": 0.126,
                 "hspace": 0.215})
        row = 2
    ax = 0

    #remove unused things
    #del names['jaccard']
    for metric in metrics:
        #print(metric)
        modes = names[metric]
        i = 0
        for mode in modes.keys():
            #print(mode)
            calcs = modes[mode]
            if (not custom):
                custom = calcs.keys()
            j = 0
            for calc in custom:
                values = calcs[calc]
                #print(faults, values)
                if (seperate):
                    axs[j, ax].plot(faults, values, str(color[i])+".-")
                    #if (rel):
                        #axs[j, ax].set_title("Comparison of the relative wasted"
                                #+" effort for the \n"+calc +" fault using the "+
                                #metric+" metric")
                    #else:
                        #axs[j, ax].set_title("Comparison of the wasted effort for the "+calc
                            #+"\nfault using the "+metric+" metric")
                    axs[j, ax].set_title(metric+" "+calc)
                    axs[j, ax].grid(True)
                    #legendloc = "upper left" if j == 1 else "upper right"
                    axs[j, ax].legend([x for x in list(modes.keys())],
                            prop={"size":12})
                else:
                    axs[int(ax/row), ax%row].plot(faults, values, str(color[i])+".-")
                j += 1
            i += 1
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
