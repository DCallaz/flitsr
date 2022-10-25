import sys
import os
import output
from merge_equiv import merge_on_row, remove_from_table
from split_faults import split

def construct_details(f):
    """
    Constructs a details object containing the information related to each
    element of the form:
    [
        (<location tuple>, [<fault_num>,...] or <fault_num> or -1),
        ...
    ]
    """
    uuts = []
    num_locs = 0
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
        uuts.append((l[0].split(":"), faults))
        num_locs += 1
        line = f.readline()
    return uuts, num_locs

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

def fill_table(tests, num_tests, locs, f):
    table = []
    groups = [[i for i in range(0, locs)]]
    counts = {"p":[0]*locs, "f":[0]*locs, "tp": 0, "tf": 0, "locs": locs}
    test_map = {}
    for r in range(0, num_tests):
        row = [True] + [False]*locs
        # Construct the table row
        line = f.readline()
        arr = line.strip().split(' ')
        for i in range(0, int(len(arr)/2)):
            pos = int(arr[i*2])
            row[pos+1] = True
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

def read_table(file_loc, split_faults):
    table = None
    tests = None
    num_locs = 0
    num_tests = 0
    details = None
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
            details,num_locs = construct_details(file)
        elif (line.startswith("#matrix")):
            # Filling the table
            table,groups,counts,test_map = fill_table(tests, num_tests, num_locs, file)
    file.close()
    if (split_faults):
        faults,unexposed = split(find_faults(details), table, groups)
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
