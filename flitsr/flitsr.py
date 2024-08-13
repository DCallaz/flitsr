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
from flitsr.output import print_csv, print_names
from flitsr.suspicious import Suspicious
from flitsr import cutoff_points
from flitsr.spectrum import Spectrum
from flitsr import score
from flitsr.args import parse_args
from flitsr.flitsr_types import Flitsr_Type
from flitsr.artemis_wrapper import run_artemis


def tests_executing(element: Spectrum.Element, spectrum: Spectrum,
                    remove=False) -> Set[Spectrum.Test]:
    """
    Finds all the test cases executing the given element, and (optionally)
    removes them from the spectrum.
    """
    executing = set()
    for test in spectrum:
        if (spectrum[test][element]):
            executing.add(test)
    if (remove):
        for test in executing:
            spectrum.remove(test)
    return executing


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
    """
    Remove the elements given by faulty from the spectrum, and remove any test
    cases executing these elements only.
    """
    # Get tests executing elems in faulty set
    executing: Set[Spectrum.Test] = set()
    for elem in faulty:
        exe = tests_executing(elem, spectrum)
        executing.update(exe)

    # Remove all elements in faulty set
    for elem in faulty:
        spectrum.remove_element(elem)

    multiFault = False
    for test in executing:
        for elem in spectrum.elements():  # remaining elements not in faulty
            if (spectrum[test][elem]):
                break
        else:
            multiFault = True
            spectrum.remove(test, hard=True)
    return multiFault


def feedback_loc(spectrum: Spectrum, formula: str,
                 artemis: bool, tiebrk: int) -> List[Spectrum.Element]:
    """Executes the recursive flitsr algorithm to identify faulty elements"""
    if (spectrum.tf == 0):
        return []
    if (artemis):
        sort = run_artemis(spectrum, formula)
    else:
        sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    s_iter = iter(sort)
    element = next(s_iter).elem
    tests_removed = tests_executing(element, spectrum, remove=True)
    while (len(tests_removed) == 0):  # sanity check
        if ((s2 := next(s_iter, None)) is None):
            count_non_removed = len(spectrum.failing)
            print("WARNING: flitsr found", count_non_removed,
                  "failing test(s) that it could not explain",
                  file=sys.stderr)
            return []
        # continue trying the next element if available
        element = s2.elem
        tests_removed = tests_executing(element, spectrum, remove=True)
    faulty = feedback_loc(spectrum, formula, artemis, tiebrk)
    remove_faulty_elements(spectrum, tests_removed, faulty)
    if (len(tests_removed) > 0):
        faulty.append(element)
    return faulty


def run(spectrum: Spectrum, formula: str, flitsr_type: Flitsr_Type,
        artemis: bool, tiebrk=0) -> score.Scores:
    if (artemis):
        sort = run_artemis(spectrum, formula)
    else:
        sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    score.set_orig(sort)
    if (flitsr_type != Flitsr_Type.BASE):
        val = 2**64
        newSpectrum = copy.deepcopy(spectrum)
        while (newSpectrum.tf > 0):
            faulty = feedback_loc(newSpectrum, formula, artemis, tiebrk)
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
            if (flitsr_type != Flitsr_Type.FLITSR_MULTI):
                break
            val = val-1
        sort.sort(True, tiebrk)
    score.unset_orig()
    return sort


def compute_cutoff(cutoff: str, sort: score.Scores, spectrum: Spectrum,
                   mode: str, effort: str) -> score.Scores:
    faults = spectrum.get_faults()
    if (cutoff.startswith("basis")):
        if ('=' in cutoff):
            num_bases = int(cutoff.split('=')[1])
        else:
            num_bases = 1
        sort = cutoff_points.basis(num_bases, spectrum, faults, sort, mode,
                                   effort=effort)
    else:
        sort = cutoff_points.cut(cutoff, spectrum, faults, sort, mode,
                                 effort=effort)
    return sort


def output(scores: score.Scores, spectrum: Spectrum, weff=[], top1=[],
           perc_at_n=[], prec_rec=[], collapse=False, csv=False, decimals=2,
           file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec):
        ties: score.Ties = scores.get_ties(spectrum, worst_effort=False)
        if (weff):
            if ("first" in weff):
                print("wasted effort (first): {:.{}f}".format(
                    weffort.first(ties, collapse),
                    decimals), file=file)
            if ("avg" in weff):
                print("wasted effort (avg): {:.{}f}".format(
                    weffort.average(ties, collapse),
                    decimals), file=file)
            if ("med" in weff):
                print("wasted effort (median): {:.{}f}".format(
                    weffort.median(ties, collapse),
                    decimals), file=file)
            if ("last" in weff):
                print("wasted effort (last): {:.{}f}".format(
                    weffort.last(ties, collapse),
                    decimals), file=file)
        if (top1):
            if ("one" in top1):
                print("at least 1 ranked #1: {:.{}f}".format(
                    top.one_top1(ties),
                    decimals), file=file)
            if ("all" in top1):
                print("all ranked #1: {:.{}f}".format(
                    top.all_top1(ties),
                    decimals), file=file)
            if ("perc" in top1):
                print("percentage ranked #1: {:.{}f}".format(
                    top.percent_top1(ties),
                    decimals), file=file)
            if ("size" in top1):
                print("size of #1: {:.{}f}".format(
                    top.size_top1(ties),
                    decimals), file=file)
        if (perc_at_n):
            bumps = percent_at_n.getBumps(ties, spectrum, collapse=collapse)
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
                    p = precision_recall.precision(entry[1], ties, spectrum,
                                                   collapse)
                    print("precision at {}: {:.{}f}".format(entry[1], p,
                                                            decimals), file=file)
                elif (entry[0] == 'r'):
                    r = precision_recall.recall(entry[1], ties, spectrum,
                                                collapse)
                    print("recall at {}: {:.{}f}".format(entry[1], r,
                                                         decimals), file=file)
    elif (csv):
        print_csv(spectrum, scores, file)
    else:
        print_names(spectrum, scores, file)


def main(argv: List[str]):
    args: Namespace = parse_args(argv[1:])
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
    if (args.input_m):
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
    # Execute techniques
    for metric in args.metrics:
        for flitsr_type in args.types:
            # Get the output channel
            if (len(args.metrics) == 1):
                output_file = args.output
            else:
                # store output files in the current directory
                input_filename = osp.basename(d_p)
                filename = (flitsr_type.value + '_' + metric + '_' +
                            input_filename)
                try:
                    output_file = open(filename, "x")
                except FileExistsError:
                    if (args.no_override):
                        # print("WARNING: Skipping execution of already "
                        #       "existing file", filename, file=sys.stderr)
                        continue
                    else:
                        print("WARNING: overriding file", filename,
                              file=sys.stderr)
                        output_file = open(filename, 'w')
            # Check for parallel
            if (args.parallel):
                spectrums = parallel.parallel(args.input, spectrum, args.tiebrk,
                                              metric, args.parallel)
            else:
                spectrums = [spectrum]
            # Run each spectrum
            for i, spectrum in enumerate(spectrums):
                if (i > 0):
                    print("<---------------------- Next Ranking ---------------------->")
                # Run techniques
                sort = run(spectrum, metric, flitsr_type, args.artemis,
                           args.tiebrk)
                # Compute cut-off
                if (args.cutoff_strategy):
                    sort = compute_cutoff(args.cutoff_strategy, sort,
                                          spectrum, metric,
                                          args.cutoff_eval)
                # Compute and print output
                output(sort, spectrum, args.weff, args.top1, args.perc_at_n,
                       args.prec_rec, args.collapse, csv=args.csv,
                       decimals=args.decimals, file=output_file)
            spectrum.reset()


if __name__ == "__main__":
    main(sys.argv)
