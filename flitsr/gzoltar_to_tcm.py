#!/usr/bin/env python3
import sys
import csv
from os import path as osp

if __name__ == "__main__":
    if (len(sys.argv) < 3):
        print("USAGE: gzoltar_to_tcm.py <gzoltar input directory> <output file>")
        quit()
    input_dir=sys.argv[1]
    output=open(sys.argv[2], 'w')
    # get tests
    print("#tests", file=output)
    test_input = csv.reader(open(osp.join(input_dir, "tests.csv")), delimiter=',')
    next(test_input)
    for test in test_input:
        outcome = "PASSED" if (test[1] == "PASS") else "FAILED"
        print(test[0], outcome, file=output)
    # get elements
    print(file=output)
    print("#uuts", file=output)
    elem_input = csv.reader(open(osp.join(input_dir, "spectra.csv")), delimiter=':')
    next(elem_input)
    for elem in elem_input:
        if (len(elem) > 2):
            print(elem[0]+":"+elem[1], " | ".join(elem[2:]), sep=" | ", file=output)
        else:
            print(elem[0]+":"+elem[1], file=output)
    # get coverage
    print(file=output)
    print("#matrix", file=output)
    cov_input = csv.reader(open(osp.join(input_dir, "matrix.txt")), delimiter=' ')
    for line in cov_input:
        indices = [i for i,e in enumerate(line) if e == "1"]
        print(*indices, sep=" 1 ", end=" 1\n", file=output)
