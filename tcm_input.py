import sys

def construct_details(f):
    uuts = []
    num_locs = 0
    line = f.readline()
    while (not line == '\n'):
        l = line.split(' ')
        uuts.append((l[0], len(l) > 1))
        num_locs += 1
        line = f.readline()
    return uuts, num_locs

def construct_table(f):
    table = []
    num_tests = 0
    line = f.readline()
    while (not line == '\n'):
        row = line.strip().split(" ")
        table.append([True] + [row[1] == 'PASSED'])
        num_tests += 1
        line = f.readline()
    return table, num_tests

def fill_table(table, f):
    for row in table:
        line = f.readline()
        arr = line.strip().split(' ')
        for i in range(0, int(len(arr)/2)):
            row[int(arr[i*2])+2] = True

def read_table(file_loc):
    table = None
    num_locs = 0
    num_tests = 0
    details = None
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
            table, num_tests = construct_table(file)
        elif (line.startswith("#uuts")):
            # Getting the details of the project
            details,num_locs = construct_details(file)
            for row in table:
                row.extend([False] * num_locs)
        elif (line.startswith("#matrix")):
            # Filling the table
            fill_table(table, file)
    file.close()
    return table,num_locs,num_tests,details

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
            print("\t("+str(name[1])+")","uut:",name[0][0], "(FAULTY)" *
                    name[0][1], file=file)
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
    actual_faults = []
    i = 0
    for uut in details:
        if (uut[1]):
            actual_faults.append(i)
        i += 1
    return actual_faults

if __name__ == "__main__":
    d = sys.argv[1]
    table,locs,tests,details = read_table(d)
    print_table(table)
