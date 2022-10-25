import sys
import re
import os
import output
from merge_equiv import merge_on_row, remove_from_table
from split_faults import split

def construct_details(f):
    uuts = []
    num_locs = 0
    bugs = 0
    f.readline()
    for line in f:
        l = line.strip().split(':')
        r = re.search("(.*)\$(.*)#([^:]*)", l[0])
        faults = []
        if (len(l) > 2):
            if (not l[2].isdigit()):
                faults = [bugs]
            else:
                faults = []
                for b in l[2:]:
                    faults.append(int(b))
            bugs += 1
        uuts.append(([r.group(1)+"."+r.group(2), r.group(3), l[1]], faults))
        num_locs += 1
    return uuts, num_locs

def construct_tests(tests_reader):
    tests = []
    num_tests = 0
    tests_reader.readline()
    for r in tests_reader:
        row = r.strip().split(",")
        tests.append(row[1] == 'PASS')
        num_tests += 1
    return tests, num_tests

def fill_table(tests, num_tests, locs, bin_file):
    table = []
    groups = [[i for i in range(0, locs)]]
    counts = {"p":[0]*locs, "f":[0]*locs, "tp": 0, "tf": 0, "locs": locs}
    test_map = {}
    for r in range(0, num_tests):
        row = [True] + [False]*locs
        line = bin_file.readline()
        arr = line.strip().split()
        for i in range(0, locs):
            if (arr[i] != "0"):
                row[i+1] = True
                if (tests[r]):
                    counts["p"][i] += 1
                else:
                    counts["f"][i] += 1
        # Use row to merge equivalences
        groups = merge_on_row(row, groups)
        # Increment total counts, and append row to table
        if (tests[r]):
            counts["tp"] += 1
        else:
            counts["tf"] += 1
            table.append(row)
            test_map[r] = len(table)-1
    groups.sort(key=lambda group: group[0])
    # Remove groupings from table
    remove_from_table(groups, table, counts)
    return table,groups,counts,test_map

def read_table(directory, split_faults):
    # Getting the details of the project
    #print("constructing details")
    details,num_locs = construct_details(open(directory+"/spectra.csv"))
    # Constructing the table
    #print("constructing table")
    tests,num_tests = construct_tests(open(directory+"/tests.csv"))
    #print("filling table")
    table,groups,counts,test_map = fill_table(tests, num_tests, num_locs, open(directory+"/matrix.txt"))
    if (split_faults):
        faults,unexposed = split(details["faults"], table, groups)
        for i in range(len(details)):
            if (i in unexposed):
                details[i] = (details[i][0], -1)
                print("Dropped faulty UUT:", details[i][0], "due to unexposure")
            for item in faults.items():
                if (i in item[1]):
                    details[i] = (details[i][0], item[0])
        if (len(faults) == 0):
            print("No exposable faults in", file_loc)
            quit()
    return table,counts,groups,details,test_map

if __name__ == "__main__":
    d = sys.argv[1]
    table,locs,tests,details = read_table(d)
    print_table(table)
