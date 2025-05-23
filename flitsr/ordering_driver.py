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
from flitsr.ranking import Ranking
from flitsr.input_type import InputType
from flitsr.errors import error
from flitsr.advanced import Config, RankerType, ClusterType


def main(argv: List[str]):
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
                output(rankings, spectrum, args.weff, args.top1, args.perc_at_n,
                       args.prec_rec, args.faults, args.collapse, csv=args.csv,
                       specCsv=args.spectrum_csv, decimals=args.decimals, file=output_file)
                spectrum.reset()


if __name__ == "__main__":
    main(sys.argv[1:])
