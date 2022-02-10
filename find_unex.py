from tcm_input import read_table, print_names, find_faults
import sys

if __name__ == "__main__":
    d = sys.argv[1]
    table,num_locs,num_tests,details = read_table(d)
    faults = []
    for i in range(0, len(details)):
        if (details[i][1]):
            faults.append(i)
    if (faults == []):
        print("no faults found")
        quit()
    if (len(sys.argv) == 3 and sys.argv[2] == "num"):
        print(len(faults))
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
