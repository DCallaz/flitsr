import sys
import re
import copy
from argparse import Namespace
from os import path as osp
from math import log
from typing import List, Set, Optional
from flitsr import weffort
from flitsr import top
from flitsr import percent_at_n
from flitsr import parallel
from flitsr import precision_recall
from flitsr.output import print_csv, print_names, find_faults, find_fault_groups
from flitsr.suspicious import Suspicious
from flitsr.cutoff_points import cutoff_points
from flitsr.spectrum import Spectrum
from flitsr import score
from flitsr.args import parse_args


def remove_from_tests(element: Spectrum.Element,
                      spectrum: Spectrum) -> Set[Spectrum.Test]:
    """Removes all the test cases executing the given element"""
    removed = set()
    for test in spectrum:
        if (spectrum[test][element]):
            removed.add(test)
    for test in removed:
        spectrum.remove(test)
    return removed


def remove_faulty_elements(spectrum: Spectrum,
                           tests_removed: Set[Spectrum.Test],
                           faulty: List[Spectrum.Element]):
    """Removes all tests that execute an 'actually' faulty element"""
    toRemove = []
    for test in tests_removed:
        for f in faulty:
            if (spectrum[test][f] is True):
                toRemove.append(test)
                break
    tests_removed.difference_update(toRemove)


def multiRemove(spectrum: Spectrum, faulty: List[Spectrum.Element]) -> bool:
    nonFaulty = set(spectrum.elements).difference(faulty)
    multiFault = False
    for test in reversed(spectrum.tests):
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


def feedback_loc(spectrum: Spectrum, formula: str,
                 tiebrk: int) -> List[Spectrum.Element]:
    """Executes the recursive flitsr algorithm to identify faulty elements"""
    if (spectrum.tf == 0):
        return []
    sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    s_iter = iter(sort)
    element = next(s_iter).elem
    tests_removed = remove_from_tests(element, spectrum)
    while (len(tests_removed) == 0):  # sanity check
        if ((s2 := next(s_iter, None)) is None):
            count_non_removed = len(spectrum.failing)
            print("WARNING: flitsr found", count_non_removed,
                  "failing test(s) that it could not explain",
                  file=sys.stderr)
            return []
        # continue trying the next element if available
        element = s2.elem
        tests_removed = remove_from_tests(element, spectrum)
    faulty = feedback_loc(spectrum, formula, tiebrk)
    remove_faulty_elements(spectrum, tests_removed, faulty)
    if (len(tests_removed) > 0):
        faulty.append(element)
    return faulty


def run(spectrum: Spectrum, formula: str, flitsr=False,
        tiebrk=0, multi=False) -> score.Scores:
    sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    score.set_orig(sort)
    if (flitsr):
        val = 2**64
        newSpectrum = copy.deepcopy(spectrum)
        while (newSpectrum.tf > 0):
            faulty = feedback_loc(newSpectrum, formula, tiebrk)
            if (not faulty == []):
                for x in sort:
                    if (x.elem in faulty):
                        x.score = val
                        val = val-1
            # Reset the coverage matrix and counts
            newSpectrum.reset()
            # Next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations
            # for the same faults
            multiRemove(newSpectrum, faulty)
            if (not multi):
                break
            val = val-1
        sort.sort(True, tiebrk)
    score.unset_orig()
    return sort


def compute_cutoff(cutoff: str, sort: score.Scores, spectrum: Spectrum,
                   mode: str, effort=2) -> score.Scores:
    fault_groups = find_fault_groups(spectrum)
    if (cutoff.startswith("basis")):
        sort = cutoff_points.basis(int(cutoff.split("=")[1]), fault_groups,
                                   sort, spectrum.groups, mode, spectrum.tf,
                                   spectrum.tp, effort=effort)
    else:
        sort = cutoff_points.cut(cutoff, fault_groups, sort, spectrum.groups,
                                 mode, spectrum.tf, spectrum.tp, effort=effort)
    return sort


def output(scores: score.Scores, spectrum: Spectrum, weff=[], top1=[],
           perc_at_n=[], prec_rec=[], collapse=False, csv=False, decimals=2,
           file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec):
        faults = find_faults(spectrum)
        if (weff):
            if ("first" in weff):
                print("wasted effort (first): {:.{}f}".format(
                    weffort.first(faults, scores, spectrum, collapse),
                    decimals), file=file)
            if ("avg" in weff):
                print("wasted effort (avg): {:.{}f}".format(
                    weffort.average(faults, scores, spectrum, collapse),
                    decimals), file=file)
            if ("med" in weff):
                print("wasted effort (median): {:.{}f}".format(
                    weffort.median(faults, scores, spectrum, collapse),
                    decimals), file=file)
            if ("last" in weff):
                print("wasted effort (last): {:.{}f}".format(
                    weffort.last(faults, scores, spectrum, collapse),
                    decimals), file=file)
        if (top1):
            if ("one" in top1):
                print("at least 1 ranked #1: {:.{}f}".format(
                    top.one_top1(faults, scores, spectrum),
                    decimals), file=file)
            if ("all" in top1):
                print("all ranked #1: {:.{}f}".format(
                    top.all_top1(faults, scores, spectrum),
                    decimals), file=file)
            if ("perc" in top1):
                print("percentage ranked #1: {:.{}f}".format(
                    top.percent_top1(faults, scores, spectrum),
                    decimals), file=file)
            if ("size" in top1):
                print("size of #1: {:.{}f}".format(
                    top.size_top1(faults, scores, spectrum),
                    decimals), file=file)
        if (perc_at_n):
            bumps = percent_at_n.getBumps(faults, scores, spectrum,
                                          collapse=collapse)
            auc = percent_at_n.auc_calc(percent_at_n.combine([(bumps[0],bumps[1:])]))
            if ('perc' in perc_at_n):
                form = ','.join(['{{:.{}f}}'.format(decimals)]*len(bumps))
                print("percentage at n:", form.format(*bumps), file=file)
            if ('auc' in perc_at_n):
                print("auc:", auc, file=file)
            if ('pauc' in perc_at_n):
                optimal = percent_at_n.auc_calc([(0.0, 100.0)])
                print("pauc:", "{:.{}f}".format(auc/optimal, decimals),
                      file=file)
            if ('lauc' in perc_at_n):
                optimal = percent_at_n.auc_calc([(0.0, 100.0)])+1
                lauc = abs(1-log(optimal-auc, optimal))
                print("lauc:", "{:.{}f}".format(lauc, decimals), file=file)
        if (prec_rec):
            for entry in prec_rec:
                if (entry[0] == 'p'):
                    p = precision_recall.precision(entry[1], faults, scores,
                                                   spectrum, collapse)
                    print("precision at {}: {:.{}f}".format(entry[1], p,
                                                            decimals), file=file)
                elif (entry[0] == 'r'):
                    r = precision_recall.recall(entry[1], faults, scores,
                                                spectrum, collapse)
                    print("recall at {}: {:.{}f}".format(entry[1], r,
                                                         decimals), file=file)
    elif (csv):
        print_csv(spectrum, scores, file)
    else:
        print_names(spectrum, scores, file)


def main(argv: List[str]):
    args: Namespace = parse_args(argv[1:])
    if (osp.isfile(args.input)):
        input_m = 1
    elif (osp.isdir(args.input) and
            osp.isfile(osp.join(args.input, "matrix.txt"))):
        input_m = 0
    else:
        print("ERROR:", args.input, "does not exist")
        quit()
    if (args.cutoff_strategy and args.cutoff_strategy.startswith('basis')):
        flitsr = True
        multi = 1
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.ranking import read_any_ranking
        scores, spectrum = read_any_ranking(args.input,
                method_level=args.method)
        output(scores, spectrum, args.weff, args.top1, args.perc_at_n,
               args.prec_rec, args.collapse, csv=args.csv,
               decimals=args.decimals, file=args.output)
        return
    # Else, run the full process
    if (input_m):
        from flitsr.tcm_input import read_spectrum
        d_p = re.sub("\\.\\w+$", ".run", args.input)
    else:
        from flitsr.input import read_spectrum
        d_p = args.input.split("/")[0] + ".run"
    # Read the spectrum in and setup parallel if needed
    spectrum = read_spectrum(args.input, args.split, method_level=args.method)
    if (spectrum is None):
        print("WARNING: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    if (hasattr(args, 'parallel') and args.parallel):
        # TODO: Fix parallel below
        # spectrums = parallel.parallel(args.input, spectrum, args.tiebrk,
        #                               args.metric, args.parallel)
        raise NotImplementedError("Parallel not supported at the moment")
    else:
        spectrums = [spectrum]
    if (args.all):  # Run the 'all' script (do all metrics and calculations)
        metrics = Suspicious.getNames()
        types = ["base_", "flitsr_", "flitsr_multi_"]
        for m in range(len(metrics)):
            for i in range(3):
                filename = types[i]+metrics[m]+"_"+d_p
                try:
                    file = open(filename, "x")
                except FileExistsError:
                    print("WARNING: overriding file", filename, file=sys.stderr)
                    file = open(filename, 'w')
                # TODO: Decide whether to include the parallel here
                # if (m == 'parallel'):
                #     spectrums = parallel.parallel(args.input, spectrum,
                #             args.tiebrk, args.metric, args.parallel)
                #     output(sort, spectrum, weff=["first","med","last"],
                #            perc_at_n=['perc'],prec_rec=[('p', 1), ('p', 5), ('p', 10),
                #                                  ('p', "f"), ('r', 1), ('r', 5),
                #                                  ('r', 10), ('r', "f")],
                #             collapse=args.collapse, file=file, decimals=args.decimals)
                # else:
                sort = run(spectrum, metrics[m], i >= 1, 3, (i == 2)*2)
                output(sort, spectrum, weff=["first", "avg", "med", "last"],
                       perc_at_n=['perc'], prec_rec=[('p', 1), ('p', 5),
                                                     ('p', 10), ('p', "f"),
                                                     ('r', 1), ('r', 5),
                                                     ('r', 10), ('r', "f")],
                       collapse=args.collapse, file=file)
                file.close()
                # end else above
                spectrum.reset()
    else:  # Just run the given metric and calculations
        for i, spectrum in enumerate(spectrums):
            if (i > 0):
                print("<---------------------- Next Ranking ---------------------->")
            sort = run(spectrum, args.metric, not args.sbfl, args.tiebrk,
                       args.multi)
            # if ('map' in counts): # Map back if parallel
            #     for rank in sort:
            #         rank[1] = counts['map'][rank[1]]
            if (args.cutoff_strategy):
                sort = compute_cutoff(args.cutoff_strategy, sort,
                                      spectrum, args.metric, args.cutoff_eval)
            output(sort, spectrum, args.weff, args.top1, args.perc_at_n,
                   args.prec_rec, args.collapse, csv=args.csv,
                   decimals=args.decimals, file=args.output)


if __name__ == "__main__":
    main(sys.argv)
