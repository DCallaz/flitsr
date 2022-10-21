import sys
from merge_equiv import merge_on_row, remove_from_table
from split_faults import split

def construct_details(f):
    details = {"files":[], "testCases":[],"fileOffsets":[],"testCaseDataSize":0,
            "faults": {}}
    i = -1
    f.readline()
    bugs = 0
    for line in f:
        l = line.strip().split(":")
        if (i >= 0 and l[0] == details["files"][i]["fileName"]):
            details["files"][i]["lineNumbers"].append(float(l[1]))
        else:
            details["files"].append({"fileName":l[0], "lineNumbers":[float(l[1])]})
            details["fileOffsets"].append(details["testCaseDataSize"])
            i += 1
        details["testCaseDataSize"] += 1
        if (len(l) > 2):
            for b in l[2:]:
                fault = bugs if (not b.isdigit()) else int(b)
                if (fault not in details["faults"]):
                    details["faults"][fault] = set()
                details["faults"][fault].add(details["testCaseDataSize"]-1)
            bugs += 1
    return details

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
    details = construct_details(open(directory+"/spectra.csv"))
    num_locs = details['testCaseDataSize']
    # Constructing the table
    #print("constructing table")
    tests,num_tests = construct_tests(open(directory+"/tests.csv"))
    #print("filling table")
    table,groups,counts,test_map = fill_table(tests, num_tests, num_locs, open(directory+"/matrix.txt"))
    if (split_faults):
        faults,unexposed = split(details["faults"], table, groups)
        details["faults"] = faults
        for unex in unexposed:
            print("Dropped faulty UUT due to unexposure:")
            print_name(find_name(details, unex, groups))
        if (len(faults) == 0):
            print("No exposable faults in", directory)
            quit()
    return table,counts,groups,details,test_map

def find_name(details, elem, groups):
    offsets = details['fileOffsets']
    for i in range(0, len(offsets)):
        if (i+1 >= len(offsets) or offsets[i+1] > elem):
            file = details['files'][i]
            filename = file['fileName'].split("/")[-1]
            line = file['lineNumbers'][elem - offsets[i]]
            faults = []
            for item in details["faults"].items():
                if (elem in item[1]):
                    faults.append(item[0])
            return (filename, line, elem, faults)

def find_names(details, faulties, groups):
    ret = []
    for faulty in faulties:
        group = []
        for elem in groups[faulty]:
            group.append(find_name(details,elem,groups))
        ret.append(group)
    return ret

def print_name(name, file=sys.stdout, indent=False):
    print("("+str(name[2])+")","File:",name[0]," | line",name[1],
        "(FAULT {})".format(",".join(str(x) for x in name[3])) if (name[3]) else "",
        file=file)

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
            print_name(name, file, indent=True)
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
    return details["faults"]

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
