import sys

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
        from input import read_table, find_faults
    else:
        from tcm_input import read_table, print_names, find_faults
    table,counts,groups,details = read_table(d)
    faults = find_faults(details)
    if (faults == []):
        print("no faults found")
        quit()
    if (num_only):
        print(len(faults))
        quit()
    ef = 0
    for f in faults:
        num = 0
        for g in range(0, len(groups)):
            if (f in groups[g]):
                num = g
                break
        found = False
        for i in range(0, len(table)):
            if (table[i][num+1]):
                found = True
                break
        if (not found):
            #print("did not find", f, num)
            print(f)
        #else:
            #print("found", f, num)
