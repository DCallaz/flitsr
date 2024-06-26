import argparse
import sys
from typing import List
from flitsr.suspicious import Suspicious
from flitsr.cutoff_points import cutoff_points


def parse_args(argv: List[str]) -> argparse.Namespace:
    """
    Parse the arguments defined by args for the flitsr program with python's
    argparse. The result is an argparse Namespace object which includes all of
    the arguments parsed (or default values).

    Args:
      argv: The list of arguments to parse, usual taken from the command
            line arguments given
    """

    # General options
    parser = argparse.ArgumentParser(prog='flitsr', description='An automatic '
            'fault finding/localization tool for multiple faults.')
    parser.add_argument('input', help='The coverage file (TCM) or '
                        'directory (GZoltar) containing the coverage collected'
                        ' for the system over the test suite')
    parser.add_argument('-o', '--output', action='store', default=sys.stdout,
            type=argparse.FileType('w'), help='Specify the output file to use '
            'for all output (default: STDOUT).')
    parser.add_argument('--csv', action='store_true',
            help='By default FLITSR will output the ranking in it\'s own '
            'FLITSR ranking format. Enabling this option will allow FLITSR to '
            'output the ranking in CSV format compatible with GZoltar\'s CSV '
            'ranking format instead.')
    parser.add_argument('-m', '--metric', action='store',
            choices=Suspicious.getNames(), default='ochiai', metavar='METRIC',
            help='The underlying (SBFL) metric to use when either ranking '
            '(if the sbfl option is given), or running the FLITSR algorithm.'
            ' Allowed values are: ['+', '.join(Suspicious.getNames())+']'
            ' (default: %(default)s)')
    parser.add_argument('-s', '--sbfl', action='store_true',
            help='Disables the FLITSR algorithm so that only the base metric '
            'is used to produce the ranking. This is equivalent to using the '
            'base metric as-is, but allows the user to run these metrics '
            'within the FLITSR framework')
    parser.add_argument('-*', '--multi', action='store_true',
            help='Runs the FLITSR* (i.e. multi-round) algorithm')
    parser.add_argument('-r', '--ranking', action='store_true',
            help='Changes flitsr\'s expected input to be an SBFL ranking in '
            'Gzoltar or FLITSR format (determined automatically), instead of '
            'the usual coverage, and produces the specified calculations '
            '(or just the ranking if no calculations are given). NOTE: any '
            'non-output based options will be ignored with this option')
    parser.add_argument('-c', '--method', action='store_true',
            help='The default for FLITSR is to use the collected coverage '
            'as-is and merely produce the ranking in terms of the names/labels'
            ' given to the elements. Alternatively, using this option, FLITSR '
            'can assume the coverage given is a statement level coverage, and '
            'will attempt to collapse this coverage to produce a method level '
            'coverage result. This collapse is done by constructing a '
            'coverage matrix with only the method names, where the execution '
            'of a method is determined by the union of the executions of its '
            'statements. Bugs added to the coverage are handled in a similar '
            'fashion.')
    parser.add_argument('--split', help='When given, this option causes faults'
            ' that are a combination of two or more sub-faults in mutually'
            ' exclusive parts of the system to be split into separate'
            ' identified faults. As a by-product this also drops faults that'
            ' are not exposed by failing tests', action='store_true')
    parser.add_argument('--collapse', action='store_true',
            help='Collapse dynamic basic-block groups into singular elements '
            'for the ranking an calculations')
    parser.add_argument('-a', '--all', action='store_true',
            help='Used in the evaluation of FLITSR against other techniques. '
            'Runs all metrics given in suspicious.py and both FLITSR and '
            'FLITSR* extensions over each metric. Also enables all of the '
            'above evaluation calculations. Prints the results out to files '
            'named [<flitsr method>_]<metric>.results for each FLITSR method '
            'and metric')
    parser.add_argument('-d', '--decimals', action='store', type=int,
            default=2, help='Sets the precision (number of decimal points) for '
            'the output of all of the calculations (default: %(default)s)')

    # Tie breaking options
    tie_grp = parser.add_argument_group('Tie breaking strategy',
            'Specifies the tie breaking strategy to use for FLITSR and the '
            'localization')
    tie_grp.add_argument('--tiebrk', action='store_const', const=1,
            default=3, help='Breaks ties using only execution counts')
    tie_grp.add_argument('--rndm', action='store_const', const=2, dest='tiebrk',
            help='Breaks ties by a randomly ordering')
    tie_grp.add_argument('--otie', action='store_const', const=3, dest='tiebrk',
            help='Breaks ties by using the original base metric ranking (in '
            'the case of FLITSR) and by execution counts otherwise')

    # Calculation options
    calc_grp = parser.add_argument_group('Calculations',
            'The following arguments replace the default ranking output of '
            'FLITSR with evaluation calculations. Multiple of the following '
            'arguments can be given in the same call')

    # Wasted effort calcuation options
    calc_grp.add_argument('--first', dest='weff', action='append_const',
            default=[], const='first',
            help='Display the wasted effort to the first fault')
    calc_grp.add_argument('--avg', '--average', dest='weff',
            action='append_const', const='avg',
            help='Display the wasted effort to the average fault')
    calc_grp.add_argument('--med', '--median', dest='weff',
            action='append_const', const='med',
            help='Display the wasted effort to the median fault')
    calc_grp.add_argument('--last', dest='weff', action='append_const',
            const='last', help='Display the wasted effort to the last fault')

    # TOP1 calculation options
    calc_grp.add_argument('--one-top1', dest='top1',
            action='append_const', const='one', default=[],
            help='Display a boolean value indicating whether at least one '
            'fault was found in the TOP1 group (elements with the highest '
            'suspiciousness')
    calc_grp.add_argument('--all-top1', dest='top1',
            action='append_const', const='all',
            help='Display the number of faults found in the top1 group')
    calc_grp.add_argument('--perc-top1', dest='top1',
            action='append_const', const='perc',
            help='Display the percentage of faults found in the top1 group')

    # Percent at n calculation options
    calc_grp.add_argument('--perc@n', '--percent-at-n', dest='perc_at_n',
            action='append_const', const='perc', default=[],
            help='Produces the percentage-at-N values (i.e. the percentage of '
            'faults found at N%% of code inspected). The output of the perc@n '
            'calculation is a list of ranks of all found faults, preceded by '
            'the number of elements in the system, which can be used to '
            'generate percentage-at-N/recall graphs')
    calc_grp.add_argument('--auc', '--area-under-curve', dest='perc_at_n',
            action='append_const', const='auc',
            help='Dislpays the area under the curve produced by the '
            'percentage-at-N calculation')
    calc_grp.add_argument('--pauc', '--percent-area-under-curve',
            dest='perc_at_n', action='append_const', const='pauc',
            help='Dislpays the area under the curve '
            'produced by the percentage-at-N calculation as a percentage of '
            'the maximum possible value (i.e. closest to perfect recall)')
    calc_grp.add_argument('--lauc', '--log-area-under-curve',
            dest='perc_at_n', action='append_const', const='lauc',
            help='Dislpays the area under the curve '
            'produced by the percentage-at-N calculation as a logarithmic '
            'percentage of the maximum possible value (i.e. closest to perfect '
            'recall). The logarithmic effect causes lower ranks to have a '
            'greater effect on the value, which corresponds to the lower ranks '
            'being more useful to the developer')

    # Precision recall type functions
    def pr(value):
        if (value == "b" or value == "f"):
            return value
        elif (value.isdigit()):
            return int(value)
        else:
            raise ValueError(str(value)+" is not a valid precision/recall "
                    "string value")
    def precision(value):
        return ('p', pr(value))
    def recall(value):
        return ('r', pr(value))

    # Precision recall calculation options
    calc_grp.add_argument('--precision-at', dest='prec_rec', metavar='x',
            action='append', default=[], type=precision,
            help='Displays precision values at a given rank `x`. Precision '
            'is the amount of faults f found within the cut-off point `x`, '
            'out of the number of elements seen (i.e. f/x). Can be specified '
            'multiple times')
    calc_grp.add_argument('--recall-at', dest='prec_rec', metavar='x',
            action='append', default=[], type=recall,
            help='Displays recall values at a given rank `x`. Recall '
            'is the amount of faults f found within the cut-off point `x`, '
            'out of the total number of faults n (i.e. f/n). Can be specified '
            'multiple times')

    # TODO: Add parallel args when implemented
    # parallel_opts = ['bdm', 'msp', 'hwk', 'vwk']
    # parser.add_argument('-p', '--parallel', action='store',
    #         choices=parallel_opts, metavar='ALGORITHM',
    #         help='Run one of the parallel debugging algorithms on the spectrum '
    #         'to produce multiple spectrums, and process all other options on '
    #         'each spectrum. Allowed values are: ['+', '.join(parallel_opts)+']')

    # TODO: Add OBA and worst args if necessary
    cut_eval_opts=['worst', 'best', 'resolve']
    parser.add_argument('--cutoff-eval', action='store', metavar='MODE',
            choices=cut_eval_opts, help='Specifies the performance mode to use '
            'when using a multi-fault fixing cut-off strategy to produce '
            'rankings. Allowed values are: ['+', '.join(cut_eval_opts)+']'+
            ' (default %(default)s)', default='best')
    cutoff_opts = cutoff_points.getNames()
    parser.add_argument('--cutoff-strategy', action='store', metavar='STRATEGY',
            choices=cutoff_opts, help='Cuts off the ranking using the given '
            'strategy\'s cut-off point. This affects both the rank output '
            'method and any calculations. Allowed values are: ['+
            ', '.join(cutoff_opts)+'] (default %(default)s). '
            'For basis, an optional value n may be given (e.g. basis=n) '
            'that determines the number of bases included before the cutoff')

    args = parser.parse_args(argv)
    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    print(args)
