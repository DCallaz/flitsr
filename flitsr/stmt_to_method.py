import sys
from os import path as osp
from typing import List
import os

if __name__ == "__main__":
    if (len(sys.argv) < 3):
        print("USAGE: python3 stmt_to_method <version> <save dir>")
        quit()
    version = sys.argv[1]
    savedir = sys.argv[2]
    spectra_lines = open(osp.join(version,"spectra.csv")).readlines()[1:]
    lines = [line.strip().split(":") for line in spectra_lines]
    coverage_all = open(osp.join(version, "matrix.txt")).readlines()
    coverage: List[List[str]] = [[] for _ in range(len(coverage_all))]
    for i in range(len(coverage_all)):
        coverage[i] = coverage_all[i].split()
    i = 0
    new_methods = []
    collapses = []
    while (i < len(lines)):
        method = lines[i][0]
        first_line = lines[i][1]
        bugs = []
        if (len(lines[i]) > 2):
            bugs.append(lines[i][2])
        j = i
        while (j+1 < len(lines) and lines[j+1][0] == method):
            j += 1
            if (len(lines[j]) > 2):
                bugs.append(lines[j][2])
        new_methods.append([method] + [first_line] + bugs)
        collapses.append((i, j))
        i = j + 1
    new_coverage = []
    for test_cov in coverage:
        new_cov = []
        x = 0
        collect = 0
        for i in range(len(test_cov)-1):
            if (i < collapses[x][0]):
                new_cov.append(test_cov[i])
            elif (i >= collapses[x][0] and i < collapses[x][1]):
                collect = collect or int(test_cov[i])
            elif (i == collapses[x][1]):
                new_cov.append(str(collect))
                collect = 0
                x += 1
            else:
                raise Exception(str(i)+" is not between range: "+str(collapses[x]))
        new_cov.append(test_cov[-1])
        new_coverage.append(new_cov)
    os.mkdir(osp.join(savedir, version))
    spec_file = open(osp.join(savedir, version, "spectra.csv"), 'w')
    spec_file.writelines([":".join(x)+"\n" for x in new_methods])
    cov_file = open(osp.join(savedir, version, "matrix.txt"), 'w')
    cov_file.writelines([" ".join(x)+"\n" for x in new_coverage])
