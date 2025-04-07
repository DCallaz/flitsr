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
from argparse import Namespace
from flitsr import parallel
from flitsr.args import parse_args
from flitsr.flitsr import output, run, compute_cutoff
from flitsr.advanced_types import AdvancedType
from flitsr.ranking import Ranking


def main(argv: List[str]):
    args: Namespace = parse_args(argv)
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
    for advanced_type in [AdvancedType.FLITSR, AdvancedType.MULTI]:
        if (AdvancedType.FLITSR in advanced_type):
            orderings = ['auto', 'conf', 'original', 'reverse', 'flitsr']
        else:
            orderings = ['original']
        for ordering in orderings:
            for metric in args.metrics:
                # Get the output channel
                input_filename = osp.basename(d_p)
                filename = (advanced_type.get_file_name() + '_' + ordering
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
                # Check for parallel
                if (AdvancedType.PARALLEL in advanced_type or metric == 'parallel'):
                    spectrums = parallel.parallel(args.input, spectrum,
                                                  args.parallel or 'msp',
                                                  method_lvl=args.method)
                    # Set default metric for parallel
                    metric = 'ochiai'
                else:
                    spectrums = [spectrum]
                rankings: List[Ranking] = []
                # Run each sub-spectrum
                for subspectrum in spectrums:
                    # Run techniques
                    ranking = run(subspectrum, metric, advanced_type, args.tiebrk,
                                  ordering)
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
