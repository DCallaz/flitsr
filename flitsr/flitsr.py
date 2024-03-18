import localize
import sys
import weffort
import top
import copy
import percent_at_n
import parallel
import precision_recall
from os import path as osp
from output import print_names, find_faults, find_fault_groups
from suspicious import Suspicious
from cutoff_points import cutoff_points


def remove_from_tests(element, spectrum):
    """Removes all the test cases executing the given element"""
    tests = set()
    for test in spectrum:
        if (spectrum[test][element]):
            spectrum.remove(test)
            tests.add(test)
    return tests


def remove_faulty_elements(spectrum, tests_removed, faulty):
    """Removes all tests that execute an 'actually' faulty element"""
    toRemove = []
    for test in tests_removed:
        for f in faulty:
            if (spectrum[test][f] == True):
                toRemove.append(test)
                break
    tests_removed.difference_update(toRemove)


def multiRemove(spectrum, faulty):
    nonFaulty = set(spectrum.elements).difference(faulty)
    multiFault = False
    for test in reversed(spectrum):
        remove = True
        for elem in nonFaulty:
            if (spectrum[test][elem]):
                remove = False
                break
        if (remove):  # this test case can be removed
            multiFault = True
            spectrum.remove(test, hard=True)
        else:  # need to remove all faults from this test case
            for elem in faulty:
                spectrum[test][elem] = False
    return multiFault


def feedback_loc(spectrum, formula, tiebrk):
    """Executes the recursive flitsr algorithm to identify faulty elements"""
    if (spectrum.tf == 0):
        return []
    sort = localize.localize(spectrum, formula, tiebrk)
    element = sort[0][1]
    tests_removed = remove_from_tests(element, spectrum)
    i = 1
    while (len(tests_removed) == 0):  # sanity check
        if (i >= len(sort)):
            count_non_removed = len(spectrum.failing)
            print("WARNING: flitsr found", count_non_removed,
                  "failing test(s) that it could not explain",
                  file=sys.stderr)
            return []
        # continue trying the next element if available
        element = sort[i][1]
        tests_removed = remove_from_tests(element, spectrum)
        i += 1
    faulty = feedback_loc(spectrum, formula, tiebrk)
    remove_faulty_elements(spectrum, tests_removed, faulty)
    if (len(tests_removed) > 0):
        faulty.append(element)
    return faulty


def run(spectrum, mode, flitsr=False, tiebrk=0, multi=0):
    sort = localize.localize(spectrum, mode, tiebrk)
    localize.orig = copy.deepcopy(sort)
    if (flitsr):
        val = 2**64
        newSpectrum = copy.deepcopy(spectrum)
        while (newSpectrum.tf > 0):
            faulty = feedback_loc(newSpectrum, mode, tiebrk)
            faulty.reverse()
            if (not faulty == []):
                for x in sort:
                    if (x[1] in faulty):
                        x[0] = val
                        val = val-1
            # The next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations for
            # the same faults
            multiRemove(newSpectrum, faulty)
            # Reset the coverage matrix and counts
            newSpectrum.reset()
            if (not multi):
                break
            val = val-1
        sort = localize.sort(sort, True, tiebrk)
    localize.orig = None
    return sort


def compute_cutoff(cutoff, sort, spectrum, mode, effort=2):
    fault_groups = find_fault_groups(spectrum)
    if (cutoff.startswith("basis")):
        sort = cutoff_points.basis(int(cutoff.split("=")[1]), fault_groups,
                                   sort, spectrum.groups, mode, spectrum.tf,
                                   spectrum.tp, effort=effort)
    else:
        sort = cutoff_points.cut(cutoff, fault_groups, sort, spectrum.groups,
                                 mode, spectrum.tf, spectrum.tp, effort=effort)
    return sort


def output(sort, spectrum, weff=None, top1=None, perc_at_n=False,
           prec_rec=None, collapse=False, file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec):
        faults = find_faults(spectrum)
        if (weff):
            if ("first" in weff):
                print("wasted effort (first):", weffort.first(faults, sort,
                    spectrum.groups, collapse), file=file)
            if ("avg" in weff):
                print("wasted effort (avg):", weffort.average(faults, sort,
                    spectrum.groups, collapse), file=file)
            if ("med" in weff):
                print("wasted effort (median):", weffort.median(faults, sort,
                    spectrum.groups, collapse), file=file)
            if ("last" in weff):
                print("wasted effort (last):", weffort.last(faults, sort,
                    spectrum.groups, collapse), file=file)
        if (top1):
            if ("one" in top1):
                print("at least 1 ranked #1:", top.one_top1(faults, sort,
                                                            spectrum.groups),
                      file=file)
            if ("all" in top1):
                print("all ranked #1:", top.all_top1(faults, sort,
                                                     spectrum.groups),
                      file=file)
            if ("perc" in top1):
                print("percentage ranked #1:", top.percent_top1(faults, sort,
                                                                spectrum.groups),
                      file=file)
            if ("size" in top1):
                print("size of #1:", top.size_top1(faults, sort, spectrum.groups),
                      file=file)
        if (perc_at_n):
            bumps = percent_at_n.getBumps(faults, sort, spectrum.groups,
                                          collapse=collapse)
            form = ','.join(['{:.3f}']*len(bumps))
            print("percentage at n:", form.format(*bumps), file=file)
        if (prec_rec):
            for entry in prec_rec:
                if (entry[0] == 'p'):
                    p = precision_recall.precision(entry[1], faults, sort, groups, collapse)
                    print("precision at {}: {}".format(entry[1], p), file=file)
                elif (entry[0] == 'r'):
                    r = precision_recall.recall(entry[1], faults, sort, groups, collapse)
                    print("recall at {}: {}".format(entry[1], r), file=file)
    else:
        names = []
        for x in sort:
            names.append(x[1])
        print_names(details, names, groups, sort, file)

def main(argv):
    metrics = Suspicious.getNames()
    cutoffs = cutoff_points.getNames()
    if (len(argv) < 2):
        print("Usage: flitsr <input file> [<metric>] [split] [method] [worst/best/resolve]"
                +" [sbfl] [first/avg/med/last] [one_top1/all_top1/perc_top1]"
                +" [perc@n] [precision/recall]@<x>"
                +" [tiebrk/rndm/otie] [multi] [parallel[=bdm/msp]] [all] [basis[=<n>]]"
                +" "+str(cutoffs))
        print()
        print("Where <metric> is one of:",metrics)
        return
    d = argv[1]
    metric = 'ochiai'
    flitsr = True
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
    parallell = None
    split = False
    method = False
    cutoff = None
    effort = 0
    ranking = False
    while (True):
        if (len(argv) > i):
            if (argv[i] in metrics):
                metric = argv[i]
            elif (argv[i].startswith("basis")):
                if ("=" in argv[i]):
                    cutoff = argv[i]
                else:
                    cutoff = "basis=1"
            elif (argv[i] in cutoffs):
                cutoff = argv[i]
            elif (argv[i] == "method"):
                method = True
            elif (argv[i] == "statement"):
                method = False
            elif (argv[i].startswith("parallel")):
                if ("=" in argv[i]):
                    parType = argv[i].split("=")[1]
                    if (parType == "bdm" or parType == "msp"
                        or parType == "hwk" or parType == "vwk"):
                        parallell = parType
                    else:
                        print("Unknown parallel argument: ", parType)
                else:
                    parallell = "bdm"
            elif (argv[i] == "split"):
                split = True
            elif (argv[i] == "worst"):
                effort = 1
            elif (argv[i] == "best"):
                effort = 0
            elif (argv[i] == "resolve"):
                effort = 2
            elif (argv[i] == "sbfl"):
                flitsr = False
            elif (argv[i] == "tcm"):
                pass
            elif (argv[i] == "first"):
                weff.append("first")
            elif (argv[i] == "avg"):
                weff.append("avg")
            elif (argv[i] == "med"):
                weff.append("med")
            elif (argv[i] == "last"):
                weff.append("last")
            elif (argv[i] == "collapse"):
                collapse = True
            elif (argv[i] == "one_top1"):
                top1.append("one")
            elif (argv[i] == "all_top1"):
                top1.append("all")
            elif (argv[i] == "perc_top1"):
                top1.append("perc")
            elif (argv[i] == "size_top1"):
                top1.append("size")
            elif (argv[i] == "perc@n"):
                perc_at_n = True
            elif ("precision@" in argv[i]):
                n = argv[i].split("@")[1]
                if (n == "b" or n == "f"):
                    prec_rec.append(('p', n))
                else:
                    prec_rec.append(('p', float(n)))
            elif ("recall@" in argv[i]):
                n = argv[i].split("@")[1]
                if (n == "b" or n == "f"):
                    prec_rec.append(('r', n))
                else:
                    prec_rec.append(('r', float(n)))
            elif (argv[i] == "tiebrk"):
                tiebrk = 1
            elif (argv[i] == "rndm"):
                tiebrk = 2
            elif (argv[i] == "otie"):
                tiebrk = 3
            elif (argv[i] == "multi"):
                multi = 1
            elif (argv[i] == "ranking"):
                ranking = True
            elif (argv[i] == "all"):
                all = True
            else:
                print("Unknown option:", argv[i])
                quit()
            i += 1
        else:
            break
    if (osp.isfile(d)):
        input_m = 1
    elif (osp.isdir(d) and osp.isfile(osp.join(d, "matrix.txt"))):
        input_m = 0
    else:
        print("ERROR:", d, "does not exist")
        quit()
    if (cutoff and cutoff.startswith('basis')):
        flitsr = True
        multi = 1
    # If only a ranking is given, print out metrics and return
    if (ranking):
        from ranking import read_any_ranking
        sort, details, groups = read_any_ranking(d, method_level=method)
        output(sort, details, groups, weff, top1, perc_at_n, prec_rec,collapse)
        return
    # Else, run the full process
    if (input_m):
        from tcm_input import read_table
        d_p = d
    else:
        from input import read_table
        d_p = d.split("/")[0] + ".txt"
    # Read the table in and setup parallel if needed
    spectrum = read_table(d, split, method_level=method)
    print("done computing spectrum")
    if (spectrum is None):
        print("WARNING: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    if (parallell):
        spectrums = parallel.parallel(d, spectrum, tiebrk, metric,
                                              parallell)
    else:
        spectrums = [spectrum]
    if (all):  # Run the 'all' script (do all metrics and calculations)
        types = ["", "flitsr_", "flitsr_multi_"]
        for m in range(len(metrics)):
            for i in range(3):
                file = open(types[i]+metrics[m]+"_"+d_p, "x")
                if (m == 'parallel'):
                    spectrums = parallel.parallel(d, spectrum, tiebrk, metric,
                                                  parallell)
                    output(sort, spectrum, weff=["first", "med", "last"],
                           perc_at_n=True,
                           prec_rec=[('p', 1), ('p', 5), ('p', 10), ('p', "f"),
                                     ('r', 1), ('r', 5), ('r', 10), ('r', "f")],
                           collapse=collapse, file=file)
                else:
                    sort = run(spectrum, metrics[m], i >= 1, 3, (i == 2)*2)
                    output(sort, spectrum, weff=["first", "avg", "med", "last"],
                           perc_at_n=True,
                           prec_rec=[('p', 1), ('p', 5), ('p', 10), ('p', "f"),
                                     ('r', 1), ('r', 5), ('r', 10), ('r', "f")],
                           collapse=collapse, file=file)
                file.close()
                spectrum.reset()
    else:  # Just run the given metric and calculations
        for i, spectrum in enumerate(spectrums):
            if (i > 0):
                print("<---------------------- Next Ranking ---------------------->")
            sort = run(spectrum, metric, flitsr, tiebrk, multi)
            # if ('map' in counts): # Map back if parallel
            #     for rank in sort:
            #         rank[1] = counts['map'][rank[1]]
            if (cutoff):
                sort = compute_cutoff(cutoff, sort, spectrum, metric, effort)
            output(sort, spectrum, weff, top1, perc_at_n, prec_rec, collapse)


if __name__ == "__main__":
    main(sys.argv)
