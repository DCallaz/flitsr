import localize
import sys
import weffort
import top
import copy
import percent_at_n
import parallel
import precision_recall

#<------------------ Outdated methods ----------------------->

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

def add_back_tests(tests_removed, table, counts):
    """Re-activates all the given tests"""
    for t in tests_removed:
        add_test(t, table, counts)

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

def remove_test(t, table, counts):
    table[t][0] = False
    counts["tf"] -= 1
    for i in range(0, counts["locs"]):
        if (table[t][i+1]):
            counts["f"][i] -= 1

def add_test(t, table, counts):
    table[t][0] = True
    counts["tf"] += 1
    for i in range(0, counts["locs"]):
        if (table[t][i+1]):
            counts["f"][i] += 1

def remove_from_tests(rule, table, counts):
    """Removes all the test cases executing the given rule"""
    tests = set()
    for i in range(0, len(table)):
        if (table[i][0] and table[i][rule+1] == True):
            #table[i][0] = False
            remove_test(i, table, counts)
            tests.add(i)
    return tests

def remove_faulty_rules(table, tests_removed, faulty):
    """Removes all tests that execute an 'actually' faulty rule"""
    toRemove = []
    for i in tests_removed:
        for f in faulty:
            if (table[i][f+1] == True):
                toRemove.append(i)
                break
    tests_removed.difference_update(toRemove)

def multiRemove(table, counts, faulty):
    nonFaulty = set(range(0, counts["locs"])).difference(faulty)
    i = 0
    multiFault = False
    for i in range(len(table)-1, -1, -1):
        row = table[i]
        remove = True
        for elem in nonFaulty:
            if (row[elem+1]):
                remove = False
                break
        if (remove): # this test case can be removed
            #print("removed test case", i)
            multiFault = True
            table.pop(i)
        else: # need to remove all faults from this test case
            for elem in faulty:
                row[elem+1] = False
                #print("removed elem", elem, "in test case", i)
    return multiFault

def reset(table, counts):
    """Re-activates all the tests and recompute scores"""
    for t in range(0, len(table)):
        if (not table[t][0]):
            add_test(t, table, counts)

spaces = -1
def feedback_loc(table, counts, formula, tiebrk):
    """Executes the recursive feedback algorithm to identify faulty rules"""
    global spaces
    if (counts["tf"] == 0):
        return []
    #print(counts)
    sort = localize.localize(counts, formula, tiebrk)
    #print(sort)
    rule = sort[0][1]
    spaces += 1
    if (sort[0][0] <= 0.0):
        #print(" "*spaces,rule,"has zero score, returning")
        return []
    #print(" "*spaces, rule,"with score",sort[0][0])
    tests_removed = remove_from_tests(rule, table, counts)
    #print(" "*spaces, "removed:",tests_removed)
    faulty = feedback_loc(table, counts, formula, tiebrk)
    remove_faulty_rules(table, tests_removed, faulty)
    if (len(tests_removed) > 0):
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
def run(table, counts, details, groups, mode='t', feedback=False, tiebrk=0,
        multi=0, weff=None, top1=None, perc_at_n=False, prec_rec=None, collapse=False, file=sys.stdout):
    sort = localize.localize(counts, mode, tiebrk)
    #print(sort)
    localize.orig = sorted(copy.deepcopy(sort), key=lambda x: x[1])
    if (feedback):
        val = 2**64
        newTable = copy.deepcopy(table)
        newCounts = copy.deepcopy(counts)
        while (newCounts["tf"] > 0):
            #print(newTable)
            faulty = feedback_loc(newTable, newCounts, mode, tiebrk)
            faulty.reverse()
            #print("faulty:",faulty)
            if (not faulty == []):
                for x in sort:
                    if (x[1] in faulty):
                        x[0] = val
                        val = val-1
            # The next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations for
            # the same faults
            multiFault = multiRemove(newTable, newCounts, faulty)
            # Reset the coverage matrix and counts
            reset(newTable, newCounts)
            if (not multi):
                #print("breaking")
                break
            #print("not breaking")
            val = val-1
        sort = localize.sort(sort, True, tiebrk)
    output(sort, details, groups, weff, top1, perc_at_n, prec_rec,collapse, file)

def output(sort, details, groups, weff, top1, perc_at_n, prec_rec, collapse, file):
    if (weff or top1 or perc_at_n or prec_rec):
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
        if (perc_at_n):
            bumps = percent_at_n.getBumps(faults, sort, groups,
                    collapse=collapse)
            form = ','.join(['{:.8%}']*len(bumps))
            print("percentage at n:", form.format(*bumps), file=file)
        if (prec_rec):
            for entry in prec_rec:
                if (entry[0] == 'p'):
                    p = precision_recall.precision(entry[1], faults, sort, groups, collapse)
                    print("precision at {}: {}".format(entry[1], p))
                elif (entry[0] == 'r'):
                    r = precision_recall.recall(entry[1], faults, sort, groups, collapse)
                    print("recall at {}: {}".format(entry[1], r))
    else:
        names = []
        for x in sort:
            names.append(x[1])
        print_names(details, names, groups, sort, file)

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Usage: feedback <input file> [tarantula/ochiai/jaccard/dstar/zoltar/barinel/hyperbolic]"
                +" [feedback] [tcm] [first/avg/med/last] [one_top1/all_top1/perc_top1]"
                +" [perc@n] [precision/recall]@x"
                +" [tiebrk/rndm/otie] [multi/multi2] [all] [only_fail]")
        exit()
    d = sys.argv[1]
    mode = 't'
    feedback = False
    input_m = 0
    i = 2
    weff = []
    top1 = []
    prec_rec = []
    perc_at_n = False
    tiebrk = 3
    multi = 0
    all = False
    collapse = False
    parallell = False
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "tarantula"):
                mode = 't'
            elif (sys.argv[i] == "ochiai"):
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
            elif (sys.argv[i] == "zoltar"):
                mode = 'z'
            elif (sys.argv[i] == "hyperbolic"):
                mode = 'y'
            elif (sys.argv[i] == "barinel"):
                mode = 'b'
            elif (sys.argv[i] == "parallel"):
                parallell = True
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
            elif (sys.argv[i] == "perc@n"):
                perc_at_n = True
            elif ("precision@" in sys.argv[i]):
                n = sys.argv[i].split("@")[1]
                if (n == "b" or n == "f"):
                    prec_rec.append(('p', n))
                else:
                    prec_rec.append(('p', float(n)))
            elif ("recall@" in sys.argv[i]):
                n = sys.argv[i].split("@")[1]
                if (n == "b" or n == "f"):
                    prec_rec.append(('r', n))
                else:
                    prec_rec.append(('r', float(n)))
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
            else:
                print("Unknown option:", sys.argv[i])
                quit()
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
    table,counts,groups,details,test_map = read_table(d)
    sort_par = None
    if (parallell or all):
        sort_par = parallel.parallel(d, table, test_map, counts, tiebrk)
        if (parallell):
            output(sort_par, details, groups, weff, top1, perc_at_n, prec_rec,
                    collapse, sys.stdout)
            quit()
    #print(table)
    #print(counts)
    #print(groups)
    #print("merging equivs")
    #groups = merge_equivs(table, num_locs)
    #print("merged")
    #print_table(table)
    if (all):
        types = ["", "flitsr_", "flitsr_multi_"]
        modes = ["tar_", "och_", "dst_"]
        for m in modes:
            for i in range(3):
            #for i in range(10):
                #d_p_s = d_p.split('.')
                #file = open("feed_rndm_"+m+d_p_s[0]+"_"+str(i)+"."+d_p_s[1], "x")
                file = open(types[i]+m+d_p, "x")
                #run(table, details, groups, only_fail, m[0], True, 2, False,
                        #weff=["first", "avg", "med"], collapse=collapse, file=file)
                run(table, counts, details, groups, m[0], i>=1, 3, (i==2)*2,
                    weff=["first", "med", "last"],top1=["perc", "size"],perc_at_n=True,
                    collapse=collapse, file=file)
                file.close()
                reset(table, counts)
    else:
        run(table, counts, details, groups, mode, feedback, tiebrk, multi, weff,
                top1, perc_at_n, prec_rec, collapse=collapse)
