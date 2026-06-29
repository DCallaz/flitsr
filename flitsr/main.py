# PYTHON_ARGCOMPLETE_OK
import sys
import copy
from os import path as osp
from typing import List, Optional, Dict, Any, Union, TextIO
from flitsr.output import print_rankings, print_spectrum_csv
from flitsr import cutoff_points
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking, Rankings
from flitsr.args import Args
from flitsr.advanced import ClusterType, RankerType
from flitsr.input.input_reader import Input
from flitsr.errors import error
from flitsr.advanced import Config
from flitsr.calculations import BUModel
from flitsr.calculations.output import calculate


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


def output(rankings: Rankings,
           calc_args: Optional[Dict[str, List[Optional[Dict[str, Any]]]]],
           decimals: int = 2, file: Union[str, TextIO] = sys.stdout, bu_model:
           BUModel = BUModel.PERFECT, collapse: bool = False, csv=False):
    if (calc_args is None):
        print_rankings(rankings, csv, file=file)
    else:
        calculate(rankings, calc_args, decimals=decimals, file=file,
                  bu_model=bu_model, collapse=collapse)


def main(argv: Optional[List[str]] = None):
    args: Args = Args(argv, cmd_line=True)
    # If only a ranking is given, print out metrics and return
    if (args.ranking):
        from flitsr.read_ranking import read_any_ranking
        rankings = read_any_ranking(args.input, method_level=args.method)
        output(rankings, args.calcs, decimals=args.decimals,
               file=args.output, bu_model=args.bug_understanding,
               collapse=args.collapse, csv=args.csv)
        return
    # Else, run the full process
    try:
        reader = Input.get_reader(args.input)
    except ValueError as e:
        error(e)
    d_p = reader.get_run_file_name(args.input)
    # Read the spectrum in and setup parallel if needed
    gspectrum = reader.read_in(args.input, args.split, args.method,
                               args.duplicates)
    if (gspectrum is None or len(gspectrum.spectrum) == 0):
        print("ERROR: Incorrectly formatted input file, terminating...",
              file=sys.stderr)
        return
    if (args.spectrum_csv):
        print_spectrum_csv(gspectrum, file=args.output)
        return
    # Execute techniques
    config: Config
    for config in args.types:
        for metric in args.metrics:
            # Get the output channel
            if (len(args.metrics) == 1 and len(args.types) == 1 and not args.all):
                output_file = args.output
            else:
                # store output files in the current directory
                input_filename = osp.basename(d_p)
                filename = (config.get_file_name(args.print_params) + '_'
                            + metric + '_' + input_filename)
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
            refiner = config.refiner(args)
            if (refiner is not None):
                spectrum = refiner.refine(spectrum, args.method)
            # Check for clustering
            cluster = config.cluster(args)
            # deal with clustering technique as metric
            if (cluster is None and hasattr(ClusterType, metric.upper())):
                metric_cluster = ClusterType[metric.upper()]
                cluster = config.build_adv_type(metric_cluster, args)
                # Set default metric for clustering
                metric = args.flitsr_default_metric
            if (cluster is not None):
                spectrums = cluster.cluster(args.input, spectrum, args.method)
            else:
                spectrums = [spectrum]
            rankings = Rankings(spectrum.get_faults(),
                                spectrum.elements())
            # Run each sub-spectrum
            for subspectrum in spectrums:
                # Run techniques
                ranker = config.ranker(args)
                if (ranker is None and hasattr(RankerType, metric.upper())):
                    metric_ranker = RankerType[metric.upper()]
                    ranker = config.build_adv_type(metric_ranker, args)
                    metric = args.flitsr_default_metric
                elif (ranker is None):
                    ranker = config.build_adv_type(RankerType['SBFL'], args)
                ranking = ranker.rank(subspectrum, metric)
                # Compute cut-off
                if (args.cutoff_strategy):
                    ranking = compute_cutoff(args.cutoff_strategy, ranking,
                                             subspectrum, metric,
                                             args.cutoff_eval)
                rankings.append(ranking)
            # Compute and print output
            output(rankings, args.calcs, decimals=args.decimals,
                   file=output_file, bu_model=args.bug_understanding,
                   collapse=args.collapse, csv=args.csv)
            spectrum.reset()


if __name__ == "__main__":
    main()
