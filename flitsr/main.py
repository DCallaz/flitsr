# PYTHON_ARGCOMPLETE_OK
import sys
import re
import copy
from os import path as osp
from math import log
from typing import List, Optional
from flitsr import weffort
from flitsr import top
from flitsr import percent_at_n
from flitsr import precision_recall
from flitsr.output import print_rankings, print_spectrum_csv
from flitsr import cutoff_points
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking, Rankings
from flitsr.tie import Ties
from flitsr.args import Args
from flitsr.advanced import ClusterType, RankerType
from flitsr.input.input_reader import Input
from flitsr.errors import error


def compute_cutoff(cutoff: str, ranking: Ranking, spectrum: Spectrum,
                   mode: str, effort: str) -> Ranking:
    faults = spectrum.get_faults()
    if (cutoff.startswith("basis")):
        if ('=' in cutoff):
            num_bases = int(cutoff.split('=')[1])
        else:
            num_bases = 1
        ranking = cutoff_points.basis(num_bases, spectrum, faults, ranking,
                                      mode, effort=effort)
    else:
        ranking = cutoff_points.cut(cutoff, spectrum, faults, ranking, mode,
                                    effort=effort)
    return ranking


def output(rankings: Rankings, weff=[], top1=[],
           perc_at_n=[], prec_rec=[], faults=[], collapse=False,
           csv=False, decimals=2, file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec or faults):
        ties: Ties = Ties(rankings)
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
            for entry in top1:
                if (entry[0] == 'all'):
                    atp = top.all_top_n(ties, entry[1], collapse=collapse)
                    print(f"all top {entry[1]}: {atp:.{decimals}f}", file=file)
                elif (entry[0] == 'one'):
                    otp = top.one_top_n(ties, entry[1], collapse=collapse)
                    print(f"one top {entry[1]}: {otp:.{decimals}f}", file=file)
        if (perc_at_n):
            bumps = percent_at_n.getBumps(ties, collapse=collapse)
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
                    p = precision_recall.precision(entry[1], ties,
                                                   collapse=collapse)
                    print("precision at {}: {:.{}f}".format(entry[1], p,
                                                            decimals), file=file)
                elif (entry[0] == 'r'):
                    r = precision_recall.recall(entry[1], ties,
                                                collapse=collapse)
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
    else:
        print_rankings(rankings, csv, file=file)


def main(argv: Optional[List[str]] = None):
    args: Args = Args(argv, cmd_line=True)
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.read_ranking import read_any_ranking
        rankings = read_any_ranking(args.input, method_level=args.method)
        output(rankings, args.weff, args.top1, args.perc_at_n,
               args.prec_rec, args.faults, args.collapse, csv=args.csv,
               decimals=args.decimals, file=args.output)
        return
    # Else, run the full process
    try:
        reader = Input.get_reader(args.input)
    except ValueError as e:
        error(e)
    d_p = reader.get_run_file_name(args.input)
    # Read the spectrum in and setup parallel if needed
    gspectrum = reader.read_spectrum(args.input, args.split, args.method)
    if (gspectrum is None or len(gspectrum.spectrum) == 0):
        print("ERROR: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    if (args.spectrum_csv):
        print_spectrum_csv(gspectrum, file=args.output)
        return
    # Execute techniques
    for config in args.types:
        for metric in args.metrics:
            # Get the output channel
            if (len(args.metrics) == 1 and len(args.types) == 1 and not args.all):
                output_file = args.output
            else:
                # store output files in the current directory
                input_filename = osp.basename(d_p)
                filename = (config.get_file_name() + '_' + metric + '_'
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
            # copy spectrum
            spectrum = copy.deepcopy(gspectrum)
            # Check for spectrum refining
            if (config.refiner is not None):
                refiner_params = args.get_arg_group(config.refiner.name)
                refiner_mthd = config.refiner.value(**refiner_params)
                spectrum = refiner_mthd.refine(spectrum, args.method)
            # Check for clustering
            if (config.cluster is not None or
                hasattr(ClusterType, metric.upper())):
                # deal with clustering technique as metric
                if (config.cluster is None):
                    cluster = ClusterType[metric.upper()]
                    # Set default metric for clustering
                    metric = args.flitsr_default_metric
                else:
                    cluster = config.cluster
                cluster_params = args.get_arg_group(cluster.name)
                cluster_mthd = cluster.value(**cluster_params)
                spectrums = cluster_mthd.cluster(args.input, spectrum,
                                                 args.method)
            else:
                spectrums = [spectrum]
            rankings = Rankings(spectrum.get_faults(),
                                spectrum.elements())
            # Run each sub-spectrum
            for subspectrum in spectrums:
                # Run techniques
                ranker = config.ranker
                if (ranker is None):
                    ranker = RankerType['SBFL']
                if (ranker == RankerType['SBFL'] and
                    hasattr(RankerType, metric.upper())):
                    ranker = RankerType[metric.upper()]
                    metric = args.flitsr_default_metric
                ranker_params = args.get_arg_group(ranker.name)
                ranker_mthd = ranker.value(**ranker_params)
                ranking = ranker_mthd.rank(subspectrum, metric)
                # Compute cut-off
                if (args.cutoff_strategy):
                    ranking = compute_cutoff(args.cutoff_strategy, ranking,
                                             subspectrum, metric,
                                             args.cutoff_eval)
                rankings.append(ranking)
            # Compute and print output
            output(rankings, args.weff, args.top1, args.perc_at_n,
                   args.prec_rec, args.faults, args.collapse, csv=args.csv,
                   decimals=args.decimals, file=output_file)
            spectrum.reset()


if __name__ == "__main__":
    main()
