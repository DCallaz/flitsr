from localize import localize
from localize import sort as loc_sort
import sys
import weffort
import top

#<------------------ Setup methods ----------------------->

def merge_equivs(table, locs):
    """Merges groups of rules with identical spectra"""
    names = [[i] for i in range(0, locs)]
    i = 0
    l = locs
    while (i < l):
        suspects = [i for i in range(i+1, l)]
        for row in table:
            if (len(suspects) == 0):
                break
            for sus in list(suspects):
                if (row[i+2] != row[sus+2]):
                    suspects.remove(sus)
        suspects.sort(reverse=True)
        for eq in suspects:
            names[i] += names[eq]
            names.pop(eq)
            for row in table:
                row.pop(eq+2)
        i += 1
        l = len(table[0])-2
    return names

#<------------------ Feedback methods ----------------------->

def all_passing(table, list=None):
    """Tests if all active test cases are passing test cases"""
    nullify = True
    if (list == None):
        list = range(0, len(table))
        nullify = False
    for i in list:
        if ((nullify or table[i][0] == True) and table[i][1] == False):
            return False
    return True

def remove_from_tests(rule, table, only_fail=False):
    """Removes all the test cases executing the given rule"""
    tests = []
    for i in range(0, len(table)):
        if (table[i][0] and (not (only_fail and table[i][1])) and table[i][rule+2] == True):
            table[i][0] = False
            tests.append(i)
    return tests

def remove_faulty_rules(table, tests_removed, faulty):
    """Removes all tests that execute an 'actually' faulty rule"""
    for i in tests_removed:
        for f in faulty:
            if (table[i][f+2] == True):
                tests_removed.remove(i)
                break

def add_back_tests(table, tests_removed):
    """Re-activates all the given tests"""
    for i in tests_removed:
        table[i][0] = True

def reset(table):
    """Re-activates all the tests"""
    for i in range(len(table)):
        table[i][0] = True

spaces = -1
def feedback_loc(table, formula, tiebrk, only_fail, deleted):
    """Executes the recursive feedback algorithm to identify faulty rules"""
    global spaces
    if (all_passing(table)):
        return []
    sort = localize(table, formula, tiebrk)
    i = 0
    rule = sort[i][1]
    spaces += 1
    while (rule in deleted):
        #print(" "*spaces, rule,"with score",sort[i][0],"[deleted]")
        i += 1
        rule = sort[i][1]
    if (sort[i][0] <= 0.0):
        #print(" "*spaces,rule,"has zero score, returning")
        return []
    #print(" "*spaces, rule,"with score",sort[i][0])
    tests_removed = remove_from_tests(rule, table, only_fail)
    #print(" "*spaces, "removed:",tests_removed)
    faulty = feedback_loc(table, formula, tiebrk, only_fail, deleted)
    remove_faulty_rules(table, tests_removed, faulty)
    if (all_passing(table, tests_removed)):
        #print(" "*spaces, rule, "all passing")
        add_back_tests(table, tests_removed)
    else:
        #print("Adding",rule)
        faulty.append(rule)
    #print(" "*spaces, rule,"finished")
    spaces -= 1
    return faulty

#<------------------ Printing methods ----------------------->

def print_table(table):
    """Prints the given table to stdout"""
    for row in table:
        for col in row:
            print(float(col), end=",")
        print()

#<------------------ Main method ----------------------->
#Description of table:
#table =
#[ <Switch>, <pass/fail>, <line 1 exe>, ..., <line n exe>
#  ..., ...
#]

def run(table, details, groups, only_fail, mode='t', feedback=False, tiebrk=False,
        multi=False, weff=None, top1=None, file=sys.stdout):
    sort = localize(table, mode, tiebrk)
    if (feedback):
        faulty = []
        val = sys.float_info.max
        while (True):
            faulty2 = feedback_loc(table, mode, tiebrk, only_fail, faulty)
            #print(faulty)
            if (not faulty2 == []):
                for x in sort:
                    if (x[1] in faulty2):
                        x[0] = val
            if (not (multi and len(faulty2) == 1)):
                #print("breaking")
                break
            #print("not breaking")
            faulty += faulty2
            val = val/10
            reset(table)
        sort = loc_sort(sort, table, True, tiebrk)
    if (weff or top1):
        faults = find_faults(details)
        if (weff):
            if ("first" in weff):
                print("wasted effort (first):", weffort.first(faults, sort,
                    groups), file=file)
            if ("avg" in weff):
                print("wasted effort (avg):", weffort.average(faults, sort,
                    groups), file=file)
            if ("med" in weff):
                print("wasted effort (median):", weffort.median(faults, sort,
                    groups), file=file)
            if ("last" in weff):
                print("wasted effort (last):", weffort.last(faults, sort,
                    groups), file=file)
        if (top1):
            if ("one" in top1):
                print("at least 1 ranked #1:", top.one_top1(faults, sort,
                    groups), file=file)
            if ("all" in top1):
                print("all ranked #1:", top.all_top1(faults, sort, groups),
                        file=file)
            if ("perc" in top1):
                print("percentage ranked #1:", top.percent_top1(faults, sort,
                    groups), file=file)
    else:
        names = []
        for x in sort:
            names.append(x[1])
        print_names(details, names, groups, sort, file)

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Usage: feedback <input file> [tarantula/ochai/jaccard/dstar/gp13/naish2/wong2]"
                +" [feedback] [tcm] [first/avg/med/last] [one_top1/all_top1/perc_top1]"
                +" [tiebrk] [multi] [all] [only_fail]")
        exit()
    d = sys.argv[1]
    mode = 't'
    feedback = False
    input_m = 0
    i = 2
    weff = []
    top1 = []
    tiebrk = False
    multi = False
    all = False
    only_fail = False
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "tarantula"):
                mode = 't'
            elif (sys.argv[i] == "ochai"):
                mode = 'o'
            elif (sys.argv[i] == "jaccard"):
                mode = 'j'
            elif (sys.argv[i] == "dstar"):
                mode = 'd'
            elif (sys.argv[i] == "gp13"):
                mode = 'g'
            elif (sys.argv[i] == "naish2"):
                mode = 'n'
            elif (sys.argv[i] == "wong2"):
                mode = 'w'
            elif (sys.argv[i] == "overlap"):
                mode = 'v'
            elif (sys.argv[i] == "harmonic"):
                mode = 'h'
            elif (sys.argv[i] == "feedback"):
                feedback = True
            elif (sys.argv[i] == "tcm"):
                input_m = 1
            elif (sys.argv[i] == "first"):
                weff.append("first")
            elif (sys.argv[i] == "avg"):
                weff.append("avg")
            elif (sys.argv[i] == "med"):
                weff.append("med")
            elif (sys.argv[i] == "last"):
                weff.append("last")
            elif (sys.argv[i] == "one_top1"):
                top1.append("one")
            elif (sys.argv[i] == "all_top1"):
                top1.append("all")
            elif (sys.argv[i] == "perc_top1"):
                top1.append("perc")
            elif (sys.argv[i] == "tiebrk"):
                tiebrk = True
            elif (sys.argv[i] == "multi"):
                multi = True
            elif (sys.argv[i] == "all"):
                all = True
            elif (sys.argv[i] == "only_fail"):
                only_fail = True
            i += 1
        else:
            break
    if (input_m):
        if (not all):
            print("Using TCM input method")
        from tcm_input import read_table, print_names, find_faults
    else:
        if (not all):
            print("Using gzoltar input method")
        from input import read_table, print_names, find_faults
    table,num_locs,num_tests,details = read_table(d)
    groups = merge_equivs(table, num_locs)
    #print_table(table)
    if (all):
        types = ["", "feed_", "feed_tie_", "feed_multi_"]
        modes = ["tar_", "och_", "jac_", "dst_"]
        for m in modes:
            for i in range(4):
                file = open(types[i]+m+d, "x")
                run(table, details, groups, only_fail, m[0], i>=1, i==2, i==3,
                        weff=["first", "avg", "last"], file=file)
                file.close()
                reset(table)

    else:
        run(table, details, groups, only_fail, mode, feedback, tiebrk, multi, weff, top1)
