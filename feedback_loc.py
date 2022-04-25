from localize import localize
from localize import sort as loc_sort
from localize import orig
import sys
import weffort
import top
import copy

#<------------------ Setup methods ----------------------->

def merge_equivs_old(table, locs):
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

def merge_equivs(table, locs):
    """Merges groups of rules with identical spectra"""
    groups = [[i for i in range(0, locs)]]
    for row in table:
        new_groups = []
        for group in groups:
            eq = [group[0]]
            neq = []
            for elem in group[1:]:
                if (row[2+elem] == row[2+group[0]]):
                    eq.append(elem)
                else:
                    neq.append(elem)
            if (eq != []):
                new_groups.append(eq)
            if (neq != []):
                new_groups.append(neq)
        groups = new_groups
    groups.sort(key=lambda group: group[0])
    remove = []
    for group in groups:
        remove.extend(group[1:])
    remove.sort(reverse=True)
    for row in table:
        for rem in remove:
            row.pop(rem+2)
    return groups

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
    tests = set()
    for i in range(0, len(table)):
        if (table[i][0] and (not (only_fail and table[i][1])) and table[i][rule+2] == True):
            table[i][0] = False
            tests.add(i)
    return tests

def remove_faulty_rules(table, tests_removed, faulty):
    """Removes all tests that execute an 'actually' faulty rule"""
    toRemove = []
    for i in tests_removed:
        for f in faulty:
            if (table[i][f+2] == True):
                toRemove.append(i)
                break
    tests_removed.difference_update(toRemove)

def add_back_tests(table, tests_removed):
    """Re-activates all the given tests"""
    for i in tests_removed:
        table[i][0] = True

def multiRemove(table, faulty):
    nonFaulty = set(range(0, len(table[0])-2)).difference(faulty)
    i = 0
    multiFault = False
    for i in range(len(table)-1, -1, -1):
        row = table[i]
        if (True):#TODO: check if failing?
            remove = True
            for elem in nonFaulty:
                if (row[elem+2]):
                    remove = False
                    break
            if (remove):#this test case can be removed
                #print("removed test case", i)
                multiFault = True
                table.pop(i)
            else:#need to remove all faults from this test case
                for elem in faulty:
                    row[elem+2] = False
                    #print("removed elem", elem, "in test case", i)
        i += 1
    return multiFault

def reset(table):
    """Re-activates all the tests"""
    for i in range(len(table)):
        table[i][0] = True

spaces = -1
def feedback_loc(table, formula, tiebrk, only_fail):
    """Executes the recursive feedback algorithm to identify faulty rules"""
    global spaces
    if (all_passing(table)):
        return []
    sort = localize(table, formula, tiebrk)
    #print(sort)
    rule = sort[0][1]
    #if (sort[0][0] == sort[1][0] and orig[sort[0][1]][0] == orig[sort[1][1]][0]
            #and orig[sort[0][1]][2] == orig[sort[1][1]][2]):
        #print("Found absolute tie:", sort[0], sort[1], orig[sort[0][1]], orig[sort[1][1]])
    spaces += 1
    if (sort[0][0] <= 0.0):
        #print(" "*spaces,rule,"has zero score, returning")
        return []
    #print(" "*spaces, rule,"with score",sort[0][0])
    tests_removed = remove_from_tests(rule, table, only_fail)
    #print(" "*spaces, "removed:",tests_removed)
    faulty = feedback_loc(table, formula, tiebrk, only_fail)
    remove_faulty_rules(table, tests_removed, faulty)
    if (all_passing(table, tests_removed)):
        #print(" "*spaces, rule, "all passing")
        add_back_tests(table, tests_removed)
    else:
        #print(" "*spaces,"Adding",rule)
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
def run(table, details, groups, only_fail, mode='t', feedback=False, tiebrk=0,
        multi=0, weff=None, top1=None, collapse=False, file=sys.stdout):
    global orig
    sort = localize(table, mode, tiebrk)
    orig = sorted(copy.deepcopy(sort), key=lambda x: x[1])
    #print(orig)
    if (feedback):
        val = sys.float_info.max
        newTable = table
        while (not all_passing(newTable)):
            #print(newTable)
            faulty = feedback_loc(newTable, mode, tiebrk, only_fail)
            #print(faulty)
            if (not faulty == []):
                for x in sort:
                    if (x[1] in faulty):
                        x[0] = val
            # Update the coverage matrix
            newTable = copy.deepcopy(newTable)#TODO: do we need to copy?
            reset(newTable)
            # The next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations for
            # the same faults
            multiFault = multiRemove(newTable, faulty)
            if (not multi or (multi == 1 and not multiFault)):
                #print("breaking")
                break
            #print("not breaking")
            val = val/10
        sort = loc_sort(sort, table, True, tiebrk)
    if (weff or top1):
        faults = find_faults(details)
        if (weff):
            if ("first" in weff):
                print("wasted effort (first):", weffort.first(faults, sort,
                    groups, collapse), file=file)
            if ("avg" in weff):
                print("wasted effort (avg):", weffort.average(faults, sort,
                    groups, collapse), file=file)
            if ("med" in weff):
                print("wasted effort (median):", weffort.median(faults, sort,
                    groups, collapse), file=file)
            if ("last" in weff):
                print("wasted effort (last):", weffort.last(faults, sort,
                    groups, collapse), file=file)
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
            if ("size" in top1):
                print("size of #1:", top.size_top1(faults, sort,
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
                +" [tiebrk/rndm/otie] [multi/multi2] [all] [only_fail]")
        exit()
    d = sys.argv[1]
    mode = 't'
    feedback = False
    input_m = 0
    i = 2
    weff = []
    top1 = []
    tiebrk = 0
    multi = 0
    all = False
    only_fail = False
    collapse = False
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
            elif (sys.argv[i] == "collapse"):
                collapse = True
            elif (sys.argv[i] == "one_top1"):
                top1.append("one")
            elif (sys.argv[i] == "all_top1"):
                top1.append("all")
            elif (sys.argv[i] == "perc_top1"):
                top1.append("perc")
            elif (sys.argv[i] == "size_top1"):
                top1.append("size")
            elif (sys.argv[i] == "tiebrk"):
                tiebrk = 1
            elif (sys.argv[i] == "rndm"):
                tiebrk = 2
            elif (sys.argv[i] == "otie"):
                tiebrk = 3
            elif (sys.argv[i] == "multi"):
                multi = 1
            elif (sys.argv[i] == "multi2"):
                multi = 2
            elif (sys.argv[i] == "all"):
                all = True
            elif (sys.argv[i] == "only_fail"):
                only_fail = True
            i += 1
        else:
            break
    if (input_m):
        from tcm_input import read_table, print_names, find_faults
        d_p = d
    else:
        from input import read_table, print_names, find_faults
        d_p = d.split("/")[0] + ".txt"
    #print("reading table")
    table,num_locs,num_tests,details = read_table(d)
    #print("merging equivs")
    groups = merge_equivs(table, num_locs)
    #print("merged")
    #print_table(table)
    if (all):
        types = ["", "feed_", "feed_multi_", "feed_multi2_"]
        modes = ["tar_", "och_", "jac_", "dst_"]
        for m in modes:
            for i in range(4):
            #for i in range(10):
                #d_p_s = d_p.split('.')
                #file = open("feed_rndm_"+m+d_p_s[0]+"_"+str(i)+"."+d_p_s[1], "x")
                file = open(types[i]+m+d_p, "x")
                #run(table, details, groups, only_fail, m[0], True, 2, False,
                        #weff=["first", "avg", "med"], collapse=collapse, file=file)
                run(table, details, groups, only_fail, m[0], i>=1, 3, (i==2) + (i==3)*2,
                        weff=["first", "avg", "med", "last"],top1=["perc", "size"], collapse=collapse, file=file)
                file.close()
                reset(table)
    else:
        run(table, details, groups, only_fail, mode, feedback, tiebrk, multi,
                weff, top1, collapse=collapse)
