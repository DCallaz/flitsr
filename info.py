from tcm_input import read_table, print_names, find_faults
import sys

if __name__ == "__main__":
    d = sys.argv[1]
    loc = int(sys.argv[2])
    table,num_locs,num_tests,details = read_table(d)
    ps = 0
    fl = 0
    ep = 0
    ef = 0
    for i in range(0, len(table)):
        if (table[i][1]):
            ps += 1
        else:
            fl += 1
        if (table[i][loc+2]):
            if (table[i][1]):
                ep += 1
            else:
                ef += 1
            print(i,table[i][1])
    print("executed pass:", ep)
    print("executed fail:", ef)
    print("passing:", ps)
    print("failing:",fl)
