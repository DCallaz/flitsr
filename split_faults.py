import sys

def getMapping(faults, groups):
    faults_comb = [i for l in faults.values() for i in l]
    mapping = {}
    for loc in faults_comb:
        for i in range(len(groups)):
            if loc in groups[i]:
                mapping[loc] = i
    return mapping

def bit(i, equiv, mapping, table):
    b = False
    for fault in equiv:
        b = b or table[i][mapping[fault]+1]
    return b

def split(faults, table, groups):
    mapping = getMapping(faults, groups)
    if (faults == {}):
        return {}, []
    ftemp = [([i], f[0], False) for f in faults.items() for i in f[1]]
    #print("Failures before", failures)
    for i in range(len(table)):
        merge = {}
        remain = []
        for equiv in ftemp:
            if (bit(i, equiv[0], mapping, table)):
                if (equiv[1] not in merge):
                    merge[equiv[1]] = []
                merge[equiv[1]] += equiv[0]
            else:
                remain.append(equiv)
        if (len(merge) != 0):
            for item in merge.items():
                remain.append((item[1], item[0], True))
        ftemp = remain
    #print(ftemp)
    fmap = {}
    unexposed = []
    for equiv in ftemp:
        if (not equiv[2]):
            unexposed.extend(equiv[0])
            continue
        if (equiv[1] not in fmap):
            fmap[equiv[1]] = []
        fmap[equiv[1]].append(equiv[0])
    new_faults = {}
    for item in fmap.items():
        if (len(item[1]) == 1):
            new_faults[item[0]] = item[1][0]
        else:
            for i in range(len(item[1])):
                new_faults[float("{}.{}".format(item[0], i+1))] = item[1][i]
    return new_faults,unexposed


if __name__ == "__main__":
    d = sys.argv[1]
    i = 2
    gzoltar = False
    num_only = False
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "gzoltar"):
                gzoltar = True
            elif (sys.argv[i] == "num"):
                num_only = True
            else:
                print("Unknown option:", sys.argv[i])
                quit()
            i += 1
        else:
            break
    if (gzoltar):
        from input import read_table, find_fault_groups, find_faults
    else:
        from tcm_input import read_table, print_names, find_fault_groups, find_faults
    table,counts,groups,details = read_table(d)
    faults = find_faults(details)
    print("faults:",faults)
    #print(groups)
    #print(table)
    faults,unexposed = split(faults, table, groups)
    print("split faults:",faults)
    print("unexposed:",unexposed)
