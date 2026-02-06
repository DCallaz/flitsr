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

import sys
from os import path as osp
from typing import List
from flitsr.args import Args
from flitsr.main import output, compute_cutoff
from flitsr.ranking import Rankings
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
        if (config.get_adv_name(RankerType) in ['FLITSR', 'MULTI']):
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
                cluster = config.cluster(args)
                # deal with clustering technique as metric
                if (cluster is None and hasattr(ClusterType, metric.upper())):
                    metric_cluster = ClusterType[metric.upper()]
                    cluster = config.run_adv_type(metric_cluster, args)
                    # Set default metric for clustering
                    metric = args.flitsr_default_metric
                if (cluster is not None):
                    spectrums = cluster.cluster(args.input, spectrum,
                                                args.method)
                else:
                    spectrums = [spectrum]
                rankings = Rankings(spectrum.get_faults(),
                                    spectrum.elements())
                # Run each sub-spectrum
                for subspectrum in spectrums:
                    # Run techniques
                    config.set_arg(RankerType['FLITSR'], 'internal_ranking',
                                   ordering)
                    ranker = config.ranker(args)
                    if (ranker is None and
                            hasattr(RankerType, metric.upper())):
                        metric_ranker = RankerType[metric.upper()]
                        ranker = config.run_adv_type(metric_ranker, args)
                        metric = args.flitsr_default_metric
                    elif (ranker is None):
                        ranker = config.run_adv_type(RankerType['SBFL'], args)
                    ranking = ranker.rank(subspectrum, metric)
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
