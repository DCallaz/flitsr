import sys
import re
import os
import output
from merge_equiv import merge_on_row, remove_from_table
from split_faults import split

def construct_details(f, method_level):
    """
    Constructs a details object containing the information related to each
    element of the form:
    [
        (<location tuple>, [<fault_num>,...] or <fault_num> or -1),
        ...
    ]
    """
    uuts = []
    num_locs = 0 # number of reported locations (methods/lines)
    i = 0 # number of actual lines
    method_map = {}
    methods = {}
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
        if (method_level):
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            if ((details[0], details[1]) not in methods):
                methods[(details[0], details[1])] = num_locs
                method_map[i] = num_locs
                uuts.append((details, faults)) # append with first line number
                num_locs += 1
            else:
                method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in uuts[method_map[i]][1]):
                        uuts[method_map[i]][1].append(fault)
                #uuts[method_map[i]][1].extend(faults)
        else:
            method_map[i] = i
            uuts.append(([r.group(1)+"."+r.group(2), r.group(3), l[1]], faults))
            num_locs += 1
        i += 1
    return uuts, num_locs, method_map

def construct_tests(tests_reader):
    tests = []
    num_tests = 0
    tests_reader.readline()
    for r in tests_reader:
        row = r.strip().split(",")
        tests.append(row[1] == 'PASS')
        num_tests += 1
    return tests, num_tests

def fill_table(tests, num_tests, locs, bin_file, method_map):
    table = []
    groups = [[i for i in range(0, locs)]]
    counts = {"p":[0]*locs, "f":[0]*locs, "tp": 0, "tf": 0, "locs": locs}
    test_map = {}
    for r in range(0, num_tests):
        row = [True] + [False]*locs
        line = bin_file.readline()
        arr = line.strip().split()
        seen = []
        for i in range(0, len(arr)-1):
            if (arr[i] != "0"):
                i = method_map[i]
                row[i+1] = row[i+1] or True
                if (i not in seen):
                    seen.append(i)
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

def read_table(directory, split_faults, method_level=False):
    # Getting the details of the project
    #print("constructing details")
    details,num_locs,method_map = construct_details(open(directory+"/spectra.csv"),
            method_level)
    # Constructing the table
    #print("constructing table")
    tests,num_tests = construct_tests(open(directory+"/tests.csv"))
    #print("filling table")
    table,groups,counts,test_map = fill_table(tests, num_tests, num_locs,
            open(directory+"/matrix.txt"), method_map)
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
