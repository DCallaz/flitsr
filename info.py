from tcm_input import read_table, print_names, find_faults
from matplotlib import pyplot as plt
import sys

if __name__ == "__main__":
    d = sys.argv[1]
    table,num_locs,num_tests,details = read_table(d)
    if (len(sys.argv) > 2):
        loc = int(sys.argv[2])
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
    else:
        uut_execs = {}
        test_execs = {}
        for row in table:
            c = row[2:].count(True)
            if (c not in test_execs):
                test_execs[c] = 0
            test_execs[c] += 1
        tableT = [list(i) for i in zip(*table)]
        for row in tableT[2:]:
            c = row[2:].count(True)
            if (c not in uut_execs):
                uut_execs[c] = 0
            uut_execs[c] += 1
        plt.bar(test_execs.keys(), test_execs.values())
        plt.xticks(list(test_execs.keys()))
        plt.xlabel("Number UUTs that were executed by the test")
        plt.ylabel("Number of tests")
        plt.show()
        plt.bar(uut_execs.keys(), uut_execs.values())
        plt.xticks(list(uut_execs.keys()))
        plt.xlabel("Number tests that executed the UUT")
        plt.ylabel("Number of UUTs")
        plt.show()
