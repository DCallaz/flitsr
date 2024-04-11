import sys
import os
from flitsr.output import find_faults, print_table
from flitsr.merge_equiv import merge_on_row, remove_from_table
from flitsr.split_faults import split

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
    line = f.readline()
    bugs = 0
    while (not line == '\n'):
        l = line.strip().split(' | ')
        faults = []
        if (len(l) > 1):
            if (not l[1].isdigit()):
                faults = [bugs]
            else:
                faults = []
                for b in l[1:]:
                    faults.append(int(b))
            bugs += 1
        if (method_level):
            details = l[0].split(":")
            if (len(details) != 3):
                print("ERROR: Could not do method level evaluation, exiting...")
                quit()
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
            uuts.append((l[0].split(":"), faults))
            num_locs += 1
        i += 1
        line = f.readline()
    #print(uuts, num_locs, method_map)
    return uuts, num_locs, method_map

def construct_tests(f):
    tests = []
    num_tests = 0
    line = f.readline()
    while (not line == '\n'):
        row = line.strip().split(" ")
        tests.append(row[1] == 'PASSED')
        num_tests += 1
        line = f.readline()
    return tests, num_tests

def fill_table(tests, num_tests, locs, f, method_map):
    table = []
    groups = [[i for i in range(0, locs)]]
    counts = {"p":[0]*locs, "f":[0]*locs, "tp": 0, "tf": 0, "locs": locs}
    test_map = {}
    for r in range(0, num_tests):
        row = [True] + [False]*locs
        # Construct the table row
        line = f.readline()
        arr = line.strip().split(' ')
        seen = []
        for i in range(0, int(len(arr)/2)):
            pos = int(arr[i*2])
            pos = method_map[pos]
            row[pos+1] = row[pos+1] or True
            if (pos not in seen):
                seen.append(pos)
                if (tests[r]):
                    counts["p"][pos] += 1
                else:
                    counts["f"][pos] += 1
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

def read_table(file_loc, split_faults, method_level=False):
    table = None
    counts = None
    test_map = None
    tests = None
    num_locs = 0
    num_tests = 0
    details = None
    method_map = None
    groups = None
    file = open(file_loc)
    while (True):
        line = file.readline()
        if (line == '' or not line.startswith("#")):
            break
        elif (line.startswith("#metadata")):
            while (not line == '\n'):
                line = file.readline()
        elif (line.startswith("#tests")):
            # Constructing the table
            tests, num_tests = construct_tests(file)
        elif (line.startswith("#uuts")):
            # Getting the details of the project
            details,num_locs,method_map = construct_details(file, method_level)
        elif (line.startswith("#matrix")):
            # Filling the table
            table,groups,counts,test_map = fill_table(tests, num_tests,
                    num_locs, file, method_map)
    file.close()
    if (split_faults):
        faults,unexposed = split(find_faults(details), table, groups)
        for i in range(len(details)):
            if (i in unexposed):
                details[i] = (details[i][0], [])
                print("Dropped faulty UUT:", details[i][0], "due to unexposure")
            fault_items = []
            for item in faults.items():
                if (i in item[1]):
                    fault_items.append(item[0])
            if (len(fault_items) != 0):
                details[i] = (details[i][0], fault_items)
        if (len(faults) == 0):
            print("No exposable faults in", file_loc)
            quit()
    return table,counts,groups,details,test_map

if __name__ == "__main__":
    d = sys.argv[1]
    table,locs,tests,details = read_table(d, False)
    print_table(table)
