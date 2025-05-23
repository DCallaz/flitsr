# PYTHON_ARGCOMPLETE_OK
import sys
import re
from argparse import Namespace
from os import path as osp
from math import log
from typing import List, Set, Optional
from flitsr import weffort
from flitsr import top
from flitsr import percent_at_n
from flitsr import precision_recall
from flitsr.output import print_csv, print_spectrum_csv, print_names
from flitsr.suspicious import Suspicious
from flitsr import cutoff_points
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking
from flitsr.tie import Ties
from flitsr.args import Args
from flitsr.advanced import ClusterType, RankerType
from flitsr.input_type import InputType
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


def output(rankings: List[Ranking], spectrum: Spectrum, weff=[], top1=[],
           perc_at_n=[], prec_rec=[], faults=[], collapse=False,
           csv=False, specCsv=False, decimals=2, file=sys.stdout):
    if (weff or top1 or perc_at_n or prec_rec or faults):
        ties: Ties = Ties(spectrum, rankings)
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
        for (i, s) in enumerate(rankings):
            if (i > 0):
                print('<', '-'*22, ' Next Ranking ', '-'*22, '>', sep='',
                      file=file)
            print_csv(spectrum, s, file)
    elif (specCsv):
        print_spectrum_csv(spectrum, file)
    else:
        for (i, s) in enumerate(rankings):
            if (i > 0):
                print('<', '-'*22, ' Next Ranking ', '-'*22, '>', sep='',
                      file=file)
            print_names(spectrum, s, file)


def main(argv: Optional[List[str]] = None):
    args: Args = Args().parse_args(argv)
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.read_ranking import read_any_ranking
        ranking, spectrum = read_any_ranking(args.input,
                                             method_level=args.method)
        output([ranking], spectrum, args.weff, args.top1, args.perc_at_n,
               args.prec_rec, args.faults, args.collapse, csv=args.csv,
               specCsv=args.spectrum_csv,
               decimals=args.decimals, file=args.output)
        return
    # Else, run the full process
    if (args.input_type is InputType.TCM):
        from flitsr.tcm_input import read_spectrum
        d_p = re.sub("\\.\\w+$", ".run", args.input)
    elif (args.input_type is InputType.GZOLTAR):
        from flitsr.input import read_spectrum
        d_p = args.input.split("/")[0] + ".run"
    else:
        error(f"Unknown input type \"{args.input_type}\", exiting...")
    # Read the spectrum in and setup parallel if needed
    spectrum = read_spectrum(args.input, args.split, method_level=args.method)
    if (spectrum is None or len(spectrum.spectrum) == 0):
        print("ERROR: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
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
            # Check for clustering
            if (config.cluster is not None or
                hasattr(ClusterType, metric.upper())):
                if (config.cluster is None):
                    cluster = ClusterType[metric.upper()]
                    # Set default metric for clustering
                    metric = 'ochiai'
                else:
                    cluster = config.cluster
                cluster_params = args.get_arg_group(cluster.name)
                cluster_mthd = cluster.value(**cluster_params)
                spectrums = cluster_mthd.cluster(args.input, spectrum,
                                                 args.method)
            else:
                spectrums = [spectrum]
            rankings: List[Ranking] = []
            # Run each sub-spectrum
            for subspectrum in spectrums:
                # Run techniques
                ranker = config.ranker
                if (ranker is None):
                    ranker = RankerType['SBFL']
                if (ranker == RankerType['SBFL'] and
                    hasattr(RankerType, metric.upper())):
                    ranker = RankerType[metric.upper()]
                    metric = 'ochiai'
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
            output(rankings, spectrum, args.weff, args.top1, args.perc_at_n,
                   args.prec_rec, args.faults, args.collapse, csv=args.csv,
                   specCsv=args.spectrum_csv, decimals=args.decimals, file=output_file)
            spectrum.reset()


if __name__ == "__main__":
    main()
