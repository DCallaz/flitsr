import sys

if __name__ == "__main__":
    d = sys.argv[1]
    if (len(sys.argv) > 3 and sys.argv[3] == "gzoltar"):
        from input import read_table, find_faults
    else:
        from tcm_input import read_table, print_names, find_faults
    table,num_locs,num_tests,details = read_table(d)
    faults = find_faults(details)
    if (faults == []):
        print("no faults found")
        quit()
    if (len(sys.argv) > 2 and sys.argv[2] == "num"):
        print(len(faults))
        quit()
    ef = 0
    for f in faults:
        found = False
        for i in range(0, len(table)):
            if (table[i][f+2]):
                if (not table[i][1]):
                    found = True
                    break
        if (not found):
            print(details[f][0], end='\n')
