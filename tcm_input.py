import sys
from merge_equiv import merge_on_row, remove_from_table
from split_faults import split

def construct_details(f):
    uuts = []
    num_locs = 0
    line = f.readline()
    bugs = 0
    while (not line == '\n'):
        l = line.strip().split(' | ')
        fault = -1
        if (len(l) > 1):
            fault = bugs if (len(l) > 2 or not l[1].isdigit()) else int(l[1])
            bugs += 1
        uuts.append((l[0], fault))
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
    groups.sort(key=lambda group: group[0])
    # Remove groupings from table
    remove_from_table(groups, table, counts)
    return table,groups,counts

def read_table(file_loc):
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
            table,groups,counts = fill_table(tests, num_tests, num_locs, file)
    file.close()
    faults,unexposed = split(find_faults(details), table, groups)
    for i in range(len(details)):
        if (i in unexposed):
            details[i] = (details[i][0], -1)
            print("Dropped faulty UUT:", details[i][0], "due to unexposure")
        for item in faults.items():
            if (i in item[1]):
                details[i] = (details[i][0], item[0])
    return table,counts,groups,details

def find_names(details, faulties, groups):
    ret = []
    for faulty in faulties:
        group = []
        for elem in groups[faulty]:
            group.append((details[elem], elem))
        ret.append(group)
    return ret

def print_names(details, faulty, groups, scores=None, file=sys.stdout):
    names = find_names(details, faulty, groups)
    i = 0
    for group in names:
        if (scores == None):
            print("Faulty grouping ("+str(faulty[i])+"): ","[", file=file)
        else:
            print("Faulty grouping ("+str(faulty[i])+"):", scores[i][0],"[",
                    file=file)
        i += 1
        for name in group:
            print("\t("+str(name[1])+")","uut:",name[0][0], "(FAULT {})".format(name[0][1])
                    if (name[0][1] != -1) else "", file=file)
        print("]", file=file)

def print_table(table):
    for row in table:
        i = 0
        p = False
        for col in row:
            if (i == 1):
                p = col
            elif (i > 1):
                print(float(col), end=" ")
            i += 1
        if (p):
            print('+')
        else:
            print('-')

def find_faults(details):
    actual_faults = {}
    i = 0
    for uut in details:
        if (uut[1] != -1):
            if (uut[1] not in actual_faults):
                actual_faults[uut[1]] = []
            actual_faults[uut[1]].append(i)
        i += 1
    return actual_faults

def find_fault_groups(details, groups):
    faults = find_faults(details)
    fault_groups = {}
    for i in range(len(groups)):
        for item in faults.items():
            fault_num = item[0]
            for loc in item[1]:
                if (loc in groups[i]):
                    if (fault_num not in fault_groups):
                        fault_groups[fault_num] = set()
                    fault_groups[fault_num].add(i)
                    break
    return fault_groups


if __name__ == "__main__":
    d = sys.argv[1]
    table,locs,tests,details = read_table(d)
    print_table(table)
