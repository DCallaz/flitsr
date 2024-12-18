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
from flitsr.tie import Ties
from flitsr.args import parse_args
from flitsr.advanced_types import AdvancedType
from flitsr.artemis_wrapper import run_artemis


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
        exe = spectrum.get_tests(elem, only_failing=True)
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


def flitsr(spectrum: Spectrum, formula: str,
           advanced_type: AdvancedType = AdvancedType.FLITSR,
           tiebrk=3) -> List[Spectrum.Element]:
    """Executes the recursive flitsr algorithm to identify faulty elements"""
    if (spectrum.tf == 0):
        return []
    if (AdvancedType.ARTEMIS in advanced_type or formula == 'artemis'):
        sort = run_artemis(spectrum, formula)
    else:
        sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    s_iter = iter(sort)
    element = next(s_iter).elem
    tests_removed = spectrum.get_tests(element, only_failing=True, remove=True)
    while (len(tests_removed) == 0):  # sanity check
        if ((s2 := next(s_iter, None)) is None):
            count_non_removed = len(spectrum.failing())
            print("WARNING: flitsr found", count_non_removed,
                  "failing test(s) that it could not explain",
                  file=sys.stderr)
            return []
        # continue trying the next element if available
        element = s2.elem
        tests_removed = spectrum.get_tests(element, only_failing=True, remove=True)
    faulty = flitsr(spectrum, formula, advanced_type, tiebrk)
    remove_faulty_elements(spectrum, tests_removed, faulty)
    if (len(tests_removed) > 0):
        faulty.append(element)
    return faulty


def flitsr_ordering(spectrum: Spectrum, basis: List[Spectrum.Element],
                    sort: score.Scores,
                    flitsr_order='auto') -> List[Spectrum.Element]:
    if (len(basis) == 0):
        return basis
    confs = []
    # check if internal ranking order needs to be determined
    if (flitsr_order in ['auto', 'conf']):
        for elem in basis:
            ts = list(spectrum.get_tests(elem, only_failing=True))
            possibles: Set[Spectrum.Element] = set()
            possibles.update(spectrum.get_executed_elements(ts[0]))
            for test in ts[1:]:
                possibles.intersection_update(spectrum.get_executed_elements(test))
            confs.append(len(possibles))
    if (flitsr_order == 'auto'):
        if (all(c > 3 for c in confs)):
            flitsr_order = 'reverse'
        elif (all(c <= 3 for c in confs)):
            flitsr_order = 'flitsr'
        else:
            flitsr_order = 'conf'
        # check for big groups
        big, small = [], []
        for elem in basis:
            if (len(spectrum.get_group(elem)) > 5):
                big.append(elem)
            else:
                small.append(elem)
        if (len(big) != 0 and len(small) != 0):
            return flitsr_ordering(spectrum, small, sort, flitsr_order) + \
                flitsr_ordering(spectrum, big, sort, flitsr_order)
    # reorder basis
    if (flitsr_order == 'flitsr'):
        ordered_basis = basis
    elif (flitsr_order == 'reverse'):
        ordered_basis = list(reversed(basis))
    elif (flitsr_order == 'original'):
        ordered_basis = []
        for x in sort:
            if (x.elem in basis):
                ordered_basis.append(x.elem)
        # add any missing elements
        if (len(ordered_basis) < len(basis)):
            ordered_basis.extend([e for e in basis if e not in ordered_basis])
    elif (flitsr_order == 'conf'):
        ordered_basis = [x for _, x in sorted(zip(confs, basis), key=lambda x:
                                              x[0])]
    return ordered_basis


def run(spectrum: Spectrum, formula: str, advanced_type: AdvancedType,
        tiebrk=0, flitsr_order='flitsr') -> score.Scores:
    if (AdvancedType.ARTEMIS in advanced_type or formula == 'artemis'):
        sort = run_artemis(spectrum, formula)
    else:
        sort = Suspicious.apply_formula(spectrum, formula, tiebrk)
    score.set_orig(sort)
    if (AdvancedType.FLITSR in advanced_type):
        val = 2**64
        newSpectrum = copy.deepcopy(spectrum)
        while (newSpectrum.tf > 0):
            basis = flitsr(newSpectrum, formula, advanced_type, tiebrk)
            if (not basis == []):
                ordered_basis = flitsr_ordering(spectrum, basis, sort,
                                                flitsr_order)
                for x in sort:
                    if (x.elem in basis):
                        x.score = val - ordered_basis.index(x.elem)
                val = val-len(basis)
            # Reset the coverage matrix and counts
            newSpectrum.reset()
            # Next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations
            # for the same faults
            multiRemove(newSpectrum, basis)
            if (AdvancedType.MULTI not in advanced_type):
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


def output(scores: List[score.Scores], spectrum: Spectrum, weff=[], top1=[],
           perc_at_n=[], prec_rec=[], faults=[], collapse=False,
           csv=False, decimals=2, file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec or faults):
        ties: Ties = Ties(spectrum, scores)
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
            for nth in [w for w in weff if type(w) == int]:
                print("wasted effort ({}): {:.{}f}".format(
                    nth, weffort.nth(ties, int(nth), collapse),
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
            if ('perc' in perc_at_n):
                form = ','.join(['{{:.{}f}}'.format(decimals)]*len(bumps))
                print("percentage at n:", form.format(*bumps), file=file)
            if (any([a in perc_at_n for a in ['auc', 'pauc', 'lauc']])):
                auc = percent_at_n.auc_calc(
                        percent_at_n.combine([(bumps[0], bumps[1:])]))
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
        if (faults):
            if ("num" in faults):
                print("fault number: {}".format(len(ties.faults)), file=file)
            if ("ids" in faults):
                print("fault ids: {}".format(list(ties.faults.keys())),
                      file=file)
            if ("elems" in faults):
                print("fault elements: {}".format([e for es in ties.faults.values()
                                                   for e in es]), file=file)
            if ("all" in faults):
                print("fault info: {}".format(ties.faults), file=file)
    elif (csv):
        for (i, s) in enumerate(scores):
            if (i > 0):
                print('<', '-'*22, ' Next Ranking ', '-'*22, '>', sep='',
                      file=file)
            print_csv(spectrum, s, file)
    else:
        for (i, s) in enumerate(scores):
            if (i > 0):
                print('<', '-'*22, ' Next Ranking ', '-'*22, '>', sep='',
                      file=file)
            print_names(spectrum, s, file)


def main(argv: List[str]):
    args: Namespace = parse_args(argv[1:])
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.ranking import read_any_ranking
        scores, spectrum = read_any_ranking(args.input,
                                            method_level=args.method)
        output([scores], spectrum, args.weff, args.top1, args.perc_at_n,
               args.prec_rec, args.faults, args.collapse, csv=args.csv,
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
    if (spectrum is None or len(spectrum.spectrum) == 0):
        print("ERROR: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    # Execute techniques
    for advanced_type in args.types:
        for metric in args.metrics:
            # Get the output channel
            if (len(args.metrics) == 1 and len(args.types) == 1 and not args.all):
                output_file = args.output
            else:
                # store output files in the current directory
                input_filename = osp.basename(d_p)
                filename = (advanced_type.get_file_name() + '_' + metric + '_'
                            + input_filename)
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
            if (AdvancedType.PARALLEL in advanced_type or metric == 'parallel'):
                spectrums = parallel.parallel(args.input, spectrum,
                                              args.parallel or 'msp',
                                              method_lvl=args.method)
                # Set default metric for parallel
                metric = 'ochiai'
            else:
                spectrums = [spectrum]
            sorts: List[score.Scores] = []
            # Run each sub-spectrum
            for subspectrum in spectrums:
                # Run techniques
                sort = run(subspectrum, metric, advanced_type, args.tiebrk,
                           args.internal_ranking)
                # Compute cut-off
                if (args.cutoff_strategy):
                    sort = compute_cutoff(args.cutoff_strategy, sort,
                                          subspectrum, metric,
                                          args.cutoff_eval)
                sorts.append(sort)
            # Compute and print output
            output(sorts, spectrum, args.weff, args.top1, args.perc_at_n,
                   args.prec_rec, args.faults, args.collapse, csv=args.csv,
                   decimals=args.decimals, file=output_file)
            spectrum.reset()


if __name__ == "__main__":
    main(sys.argv)
