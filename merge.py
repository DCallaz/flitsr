import sys
from percent_at_n import combine,auc_calc
import os
from file import File
from suspicious import Suspicious

if __name__ == "__main__":
    #metrics = [("tar_", "Tarantula"), ("och_", "Ochiai"), ("dst_", "DStar")]
    #metrics = [("tar_", "Tarantula"), ("och_", "Ochiai"), ("dst_", "DStar"),
               #("jac_", "Jaccard"), ("gp13_", "GP13"), ("nai_", "naish2"),
               #("ovr_", "Overlap"), ("harm_", "Harmonic"), ("zol_", "Zoltar"),
               #("hyp_", "Hyperbolic"), ("bar_", "Barinel")]#, ("par_", "Parallel")]
    metrics = Suspicious.getNames()
    modes = [("", "Base metric"), ("flitsr_", "FLITSR"),
            ("flitsr_multi_", "FLITSR*")]
    calcs = ["first",
            "avg",
            "med",
            "last",
            #"top1",
            #"sizet1",
            "perc@n",
            "precision at 1",
            "precision at 5",
            "precision at 10",
            "precision at num faults",
            "recall at 1",
            "recall at 5",
            "recall at 10",
            "recall at num faults"
            ]
    perc_file = open("perc_at_n_results", "w")
    files = {}
    total = 0
    avgs = []
    rel = False
    recurse = False
    max = None
    i = 1
    ns = []
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "rel"):
                rel = True
            elif (sys.argv[i].startswith("recurse")):
                recurse = True
                if ("=" in sys.argv[i]):
                    max = int(sys.argv[i].split("=")[1])
            elif (sys.argv[i].startswith("n")):
                a = sys.argv[i].split("=")[1]
                ns = [int(x) for x in a.split(",")]
            else:
                print("Unknown option:", sys.argv[i])
                quit()
            i += 1
        else:
            break

    def find_dirs(dirs, path, depth=1, max=None):
        for dir in os.scandir(path):
            if (dir.is_dir()):
                new_path = dir.path
                if ((max and depth >= max) or
                    (not max and dir.name.endswith("-fault") and
                        (len(ns) == 0 or int(dir.name.split("-")[0]) in ns) )):
                    dirs.append(new_path+"/")
                else:
                    find_dirs(dirs, new_path, depth=depth+1, max=max)

    if (rel):
        if (not recurse):
            size = int(open("../size").readline())
    dirs = [""]
    if (recurse):
        dirs = []
        find_dirs(dirs, ".", max=max)

    for metric in metrics:
        for mode in modes:
            for calc in calcs:
                if (calc == "perc@n"):
                    avgs.append([])
                else:
                    avgs.append(0)

    if (rel):
        sizes = {}
    for d in dirs:
        files[d] = []
        for metric in metrics:
            for mode in modes:
                files[d].append(File(d+mode[0]+metric+"_"+"weff"))
                if (rel):
                    sizes[d] = int(open(d+"../size").readline())

    end = False
    while (not end):
        for d in dirs:
            lines = []
            for f in files[d]:
                f.readline()
                for calc in calcs:
                    lines.append(f.readline())
                f.readline()
            if (lines[0] == ''):
                end = True
                break
            total += 1
            for i in range(0, len(lines)):
                if (type(avgs[i]) == list):
                    vals = lines[i].strip().split(": ")[1].split(",")
                    #TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    total = vals[0]
                    avgs[i].append([float(x) for x in vals[1:]])
                elif (rel):
                    if (recurse):
                        avgs[i] += float(lines[i].split(": ")[1])*100/sizes[d]
                    else:
                        avgs[i] += float(lines[i].split(": ")[1])*100/size
                else:
                    avgs[i] += float(lines[i].split(": ")[1])

    i = 0
    for metric in metrics:
        print(metric.capitalize())
        if ("perc@n" in calcs):
            print(metric.capitalize(), file=perc_file)
        for mode in modes:
            print('\t', mode[1])
            if ("perc@n" in calcs):
                print('\t', mode[1], file=perc_file)
            for calc in calcs:
                if (calc == "perc@n"):
                    comb = combine(avgs[i])
                    print("\t\t",calc+":", comb, file=perc_file)
                elif (rel):
                    avgs[i] = avgs[i]/total
                    print("\t\t",calc+":", str(avgs[i])+"%")
                else:
                    avgs[i] = avgs[i]/total
                    print("\t\t",calc+":", avgs[i])
                i += 1
