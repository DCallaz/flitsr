import sys
import re
from flitsr.percent_at_n import combine
import os
from os import path as osp
from flitsr.file import File
from typing import Set, Dict, List, Any

PERC_N = "percentage at n"


def readBlock(file: File) -> List[str]:
    block = []
    line = file.readline()
    if (": " not in line):
        line = file.readline()
    while (line != "" and not re.match("^-+$", line)):
        block.append(line)
        line = file.readline()
    return block


if __name__ == "__main__":
    metrics: Set[str] = set()
    modes: Set[str] = set()
    calcs: Set[str] = set()
    #           dir       mode      metric
    files: Dict[str, Dict[str, Dict[str, File]]] = {}
    #          mode      metric    calc
    avgs: Dict[str, Dict[str, Dict[str, Any]]] = {}
    total = 0
    rel = False
    recurse = False
    tex = False
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
            elif (sys.argv[i] == "tex"):
                tex = True
            else:
                print("Unknown option:", sys.argv[i])
                quit()
            i += 1
        else:
            break

    # Initialize the script
    def find_dirs(dirs: List[str], path, depth=1, max=None):
        for dir in os.scandir(path):
            if (dir.is_dir()):
                new_path = dir.path
                if ((max and depth >= max) or
                    (not max and any(f.endswith('.results') for f in
                                     os.listdir(new_path)))):
                    if (len(ns) == 0 or int(dir.name.split("-")[0]) in ns):
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

    if (rel):
        sizes = {}
    results_check = re.compile("^(?:([\\w_]*)_)?(\\w+)\\.results$")
    for d in dirs:
        files.setdefault(d, {})
        for file in os.scandir(osp.normpath(d)):
            m = results_check.match(file.name)
            if (m):
                mode = m.group(1) or ""
                modes.add(mode)
                metric = m.group(2)
                metrics.add(metric)
                files[d].setdefault(mode, {})[metric] = File(file)
                avgs.setdefault(mode, {}).setdefault(metric, {})
        if (rel):
            sizes[d] = int(open(osp.join(d, "../size")).readline())

    # Collect all the results
    class Avg:
        """Holds a partially constructed average"""
        def __init__(self):
            self.sum = 0.0
            self.adds = 0

        def add(self, val):
            self.sum += val
            self.adds += 1

        def eval(self):
            return self.sum/self.adds

    for d in dirs:
        for mode in modes:
            for metric in metrics:
                block = readBlock(files[d][mode][metric])
                while (block != []):
                    for line in block:
                        line_s = line.split(": ")
                        calc = line_s[0]
                        calcs.add(calc)
                        if (calc == PERC_N):
                            vals = line_s[1].split(",")
                            avgs[mode][metric].setdefault(calc, []).append(
                                (float(vals[0]), [float(x) for x in vals[1:]]))
                        elif (rel):
                            if (recurse):
                                avgs[mode][metric].setdefault(calc, Avg()).add(
                                        float(line_s[1])*100/sizes[d])
                            else:
                                avgs[mode][metric].setdefault(calc, Avg()).add(
                                        float(line_s[1])*100/size)
                        else:
                            avgs[mode][metric].setdefault(calc, Avg()).add(
                                    float(line_s[1]))
                    block = readBlock(files[d][mode][metric])

    # Set up output files
    perc_file = open("perc_at_n"+"-".join([str(n) for n in ns])+"_results", "w")
    i = 0
    tex_file = None
    if (tex):
        tex_file = open("results"+'-'.join([str(n) for n in ns])+".tex", "w")
        print("\\documentclass{standalone}", file=tex_file)
        # print("\\usepackage{longtable}", file=tex_file)
        print("\\begin{document}", file=tex_file)
        # print("\\begin{longtable}", file=tex_file)
        print("\\begin{tabular}{"+'|'.join(['c']*(len(calcs)+1))+"}",
              file=tex_file)
        print("Metric & "+' & '.join([c for c in sorted(calcs) if c != PERC_N])+"\\\\",
              file=tex_file)

    # Print out merged results
    for metric in sorted(metrics):
        print(metric.capitalize())
        if (PERC_N in calcs):
            print(metric.capitalize(), file=perc_file)
        for mode in sorted(modes):
            print('\t', mode.replace("_", " ").title())
            if (PERC_N in calcs):
                print('\t', mode.replace("_", " ").title(), file=perc_file)
            if (tex):
                print('%25s' % (metric.capitalize() + " " +
                                mode.replace("_", " ").title()), end=" & ",
                      file=tex_file)
            for j, calc in enumerate(sorted(calcs)):
                if (calc == PERC_N):
                    comb = combine(avgs[mode][metric][calc])
                    print("\t\t", calc+":", comb, file=perc_file)
                elif (rel):
                    result = avgs[mode][metric][calc].eval()
                    print("\t\t", calc+":", str(result)+"%")
                    if (tex):
                        end = (" & " if j+1 != len(calcs) else " \\\\\n")
                        print('% 10.4f' % result+"%", end=end, file=tex_file)
                else:
                    result = avgs[mode][metric][calc].eval()
                    print("\t\t", calc+":", result)
                    if (tex):
                        end = (" & " if j+1 != len(calcs) else " \\\\\n")
                        print('% 10.4f' % result, end=end, file=tex_file)
                i += 1
    if (tex):
        print("\\end{tabular}", file=tex_file)
        # print("\\end{longtable}", file=tex_file)
        print("\\end{document}", file=tex_file)
