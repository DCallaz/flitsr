import sys
from percent_at_n import combine
import os
from file import File

if __name__ == "__main__":
    #metrics = [("tar_", "Tarantula"), ("och_", "Ochiai"), ("dst_", "DStar")]
    metrics = [("tar_", "Tarantula"), ("och_", "Ochiai"), ("dst_", "DStar"),
               ("jac_", "Jaccard"), ("gp13_", "GP13"), ("nai_", "naish2"),
               ("ovr_", "Overlap"), ("harm_", "Harmonic"), ("zol_", "Zoltar"),
               ("hyp_", "Hyperbolic"), ("bar_", "Barinel")]#, ("par_", "Parallel")]
    modes = [("", "Base metric"), ("flitsr_", "FLITSR"), #("feed_tie_", "feedback tie"),
            #("feed_multi_", "feedback multi"),
            ("flitsr_multi_", "FLITSR*")]
            #("feed_rndm_max_", "feedback random max"), ("feed_rndm_avg_",
            #"feedback random average"), ("feed_rndm_min_", "feedback random min")]
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
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "rel"):
                size = int(open("../size").readline())
                rel = True
            elif (sys.argv[i].startswith("recurse")):
                recurse = True
                if ("=" in sys.argv[i]):
                    max = int(sys.argv[i].split("=")[1])
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
                if ((max and depth >= max) or (not max and dir.name.endswith("-fault"))):
                    dirs.append(new_path+"/")
                else:
                    find_dirs(dirs, new_path, depth=depth+1, max=max)

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

    for d in dirs:
        files[d] = []
        for metric in metrics:
            for mode in modes:
                files[d].append(File(d+mode[0]+metric[0]+"weff"))

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
                    avgs[i].append([float(x) for x in lines[i].strip().split(": ")[1][:-1].split("%,")])
                elif (rel):
                    avgs[i] += float(lines[i].split(": ")[1])*100/size
                else:
                    avgs[i] += float(lines[i].split(": ")[1])

    i = 0
    for metric in metrics:
        print(metric[1])
        if ("perc@n" in calcs):
            print(metric[1], file=perc_file)
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
