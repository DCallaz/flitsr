"""
This is a custom driver for running flitsr that facilitates the flitsr basis
ordering experiments.

The driver runs flitsr with each of its basis ordering types and stores each
result. The driver mostly mimicks the main method in the flitsr module (i.e.
the main entry point of flitsr), and uses the same command line arguments. The
main difference is the restriction to only running techniques with flitsr
activated (no base SBFL techniques) and running all variants of the flitsr
basis orderings on these.
"""


import re
import sys
from os import path as osp
from typing import List
from flitsr.args import Args
from flitsr.main import output, compute_cutoff
from flitsr.ranking import Ranking, Rankings
from flitsr.input.input_reader import Input
from flitsr.errors import error
from flitsr.advanced import Config, RankerType, ClusterType
from flitsr.output import print_spectrum_csv


def main(argv: List[str]):
    args: Args = Args(argv, cmd_line=True)
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.read_ranking import read_any_ranking
        rankings = read_any_ranking(args.input,
                                    method_level=args.method)
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
    spectrum = reader.read_spectrum(args.input, args.split, args.method)
    if (spectrum is None or len(spectrum.spectrum) == 0):
        print("ERROR: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    if (args.spectrum_csv):
        print_spectrum_csv(spectrum, file=args.output)
        return
    # Execute techniques
    for config in [Config(RankerType['FLITSR']),
                   Config(RankerType['MULTI'])]:
        if (config.ranker is RankerType['FLITSR'] or
            config.ranker is RankerType['MULTI']):
            orderings = ['auto', 'conf', 'original', 'reverse', 'flitsr']
        else:
            orderings = ['original']
        for ordering in orderings:
            for metric in args.metrics:
                # Get the output channel
                input_filename = osp.basename(d_p)
                filename = (config.get_file_name() + '_' + ordering
                            + '_' + metric + '_' + input_filename)
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
                    # updated the internal ranking
                    args.flitsr_internal_ranking = ordering
                    ranker_params = args.get_arg_group(ranker.name)
                    if ('internal_ranking' in ranker_params):
                        ranker_params['internal_ranking'] = ordering
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
    main(sys.argv[1:])
