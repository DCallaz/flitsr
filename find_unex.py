import sys

#TODO: Handle multi-location faults and merging properly
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
    faults = find_fault_groups(details, groups)
    if (faults == []):
        print("no faults found")
        quit()
    if (num_only):
        print(len(faults))
        quit()
    ef = 0

    print(faults)
    print(groups)
    print(table)

    def bit(i, group, table):
        b = False
        for failure in group:
            b = b or table[failure][i]
        return b

    def inSub(f, faults):
        for item in faults.items():
            if (f in item[1]):
                return item[0]
        return None

    failures = [[i] for i in range(len(table))]
    #print("Failures before", failures)
    for i in range(1, len(table[0])):
        merge = []
        remain = []
        for equiv in failures:
            if (bit(i, equiv, table)):
                merge += equiv #the "one" array contains merged groups
            else:
                remain.append(equiv) # the "zero" array contains unmerged groups
        if (len(merge) != 0):
            remain.append(merge)
        failures = remain

    #print("Failures after", failures)
    unexposed = []
    executed = [[] for _ in range(len(failures))]
    for i in range(1, len(table[0])):
        f = i - 1
        found = inSub(f, faults)
        if (found != None):
            exe = False
            for j in range(len(failures)):
                if (bit(i, failures[j], table)):
                    exe = True
                    executed[j] += groups[f]
            if (not exe):
                unexposed += groups[f]

    print("unexposed", unexposed)
    for j in range(len(failures)):
        print(failures[j], executed[j])
