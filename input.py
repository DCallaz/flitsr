import sys

def construct_details(f):
    details = {"files":[], "testCases":[],"fileOffsets":[],"testCaseDataSize":0,
            "faults": []}
    i = -1
    f.readline()
    for line in f:
        l = line.strip().split(":")
        if (i >= 0 and l[0] == details["files"][i]["fileName"]):
            details["files"][i]["lineNumbers"].append(float(l[1]))
        else:
            details["files"].append({"fileName":l[0], "lineNumbers":[float(l[1])]})
            details["fileOffsets"].append(details["testCaseDataSize"])
            i += 1
        details["testCaseDataSize"] += 1
        if (len(l) > 2 and l[2] == "FAULT"):
            details["faults"].append(details["testCaseDataSize"]-1)
    return details

def construct_table(num_locs, tests_reader):
    table = []
    tests_reader.readline()
    i = 0
    for r in tests_reader:
        row = r.strip().split(",")
        table.append([True] + [row[1] == 'PASS'] + [False]*(num_locs))
        i += 1
    return table, i

def fill_table(table, locs, bin_file):
    j = 0
    for row in table:
        line = bin_file.readline()
        arr = line.strip().split()
        if (not len(arr)-1 == locs):
            print("WARING number of locations != line, locs:",locs,"line:",len(arr)-1)
        for i in range(0, locs):
            n = arr[i]
            row[i+2] = True if (float(n) == 1) else False
        if (not (arr[-1] == '+') == row[1]):
            print("WARNING: test file and matrix do not agree on line",j)
            print("Test file has",row[1], "and matrix has", arr[-1])
            print("Keeping matrix result")
            row[1] = (arr[-1] == '+')
        j = j+1

def read_table(directory):
    # Getting the details of the project
    #print("constructing details")
    details = construct_details(open(directory+"/spectra.csv"))
    num_locs = details['testCaseDataSize']
    # Constructing the table
    #print("constructing table")
    table,num_tests = construct_table(num_locs, open(directory+"/tests.csv"))
    #print("filling table")
    fill_table(table, num_locs, open(directory+"/matrix.txt"))
    return table,num_locs,num_tests,details

def find_names(details, faulties, groups):
    ret = []
    for faulty in faulties:
        group = []
        for elem in groups[faulty]:
            offsets = details['fileOffsets']
            for i in range(0, len(offsets)):
                if (i+1 >= len(offsets) or offsets[i+1] > elem):
                    file = details['files'][i]
                    filename = file['fileName'].split("/")[-1]
                    line = file['lineNumbers'][elem - offsets[i]]
                    fault = elem in details["faults"]
                    group.append((filename, line, elem, fault))
                    break
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
            print("("+str(name[2])+")","File:",name[0]," | line",name[1],
                "(FAULTY)" * name[3], file=file)
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

if __name__ == "__main__":
    d = sys.argv[1]
    table,locs,tests,details = read_table(d)
    print_table(table)
