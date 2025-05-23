from __future__ import annotations
import argparse
import argcomplete
import inspect
import sys
from pathlib import Path
from os import path as osp
from typing import List, Dict, Any, Optional
from flitsr.suspicious import Suspicious
from flitsr import cutoff_points
from flitsr.singleton import SingletonMeta
# from flitsr.advanced_types import AdvancedType
from flitsr.input_type import InputType
from flitsr import advanced
from flitsr.advanced import Config


class Args(argparse.Namespace, metaclass=SingletonMeta):
    def _add_params(self, params: argparse.Namespace):
        dict_ = vars(params)
        for key in dict_:
            setattr(self, key, dict_[key])

    def parse_args(self, argv: Optional[List[str]]) -> Args:
        """
        Parse the arguments defined by args for the flitsr program with
        python's argparse. The result is an argparse Namespace object which
        includes all of the arguments parsed (or default values).

        Args:
          argv: The list of arguments to parse, usual taken from the command
                line arguments given
        """
        # Check file exists function
        def check_file(filename):
            if (osp.exists(filename)):
                return filename
            else:
                raise argparse.ArgumentTypeError('Could not find input file:'
                                                 f' \"{filename}\"')

        # check FLITSR type combinations function
        def check_type(type_comb: str):
            type_sep = type_comb.split('+')
            cluster = None
            ranker = None
            for t in type_sep:
                t = t.upper()
                if (hasattr(advanced.ClusterType, t)):
                    if (cluster is not None):
                        raise argparse.ArgumentTypeError('Cannot have two '
                            f'cluster types: {cluster.name} and {t}')
                    cluster = advanced.ClusterType[t]
                elif (hasattr(advanced.RankerType, t)):
                    if (ranker is not None):
                        raise argparse.ArgumentTypeError('Cannot have two '
                            f'ranker types: {ranker.name} and {t}')
                    ranker = advanced.RankerType[t]
                else:
                    raise argparse.ArgumentTypeError('Invalid type for '
                                                     f'--all-types: \"{t}\"')
            adv_type = Config(ranker, cluster)
            return adv_type

        # General options
        parser = argparse.ArgumentParser(prog='flitsr', description='An automatic '
                'fault finding/localization tool for multiple faults.')
        parser.add_argument('input', type=check_file,
                            help='The coverage file (TCM) or '
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
        parser.add_argument('--spectrum-csv', action='store_true',
                help='Enabling this option will cause FLITSR to '
                'output the spectrum in CSV format.')
        default_metric = 'ochiai'
        parser.add_argument('-m', '--metric', dest='metrics', action='append',
                choices=Suspicious.getNames(True), metavar='METRIC',
                help='The underlying (SBFL) metric(s) to use when either ranking '
                '(if the sbfl option is given), or running the FLITSR algorithm. '
                'Option may be supplied multiple times to run multiple metrics. '
                'Specifying multiple metrics will output the results of each '
                'metric to a seperate file using the metric\'s name instead of '
                'stdout. Allowed values are: ['+', '.join(Suspicious.getNames(True))+'] '
                '(default: {})'.format(default_metric))
        parser.add_argument('-r', '--ranking', action='store_true',
                help='Changes FLITSR\'s expected input to be an SBFL ranking in '
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
                'named [<flitsr method>_]<metric>.run for each FLITSR method '
                'and metric')
        adv_types = list(advanced.all_types.keys())
        parser.add_argument('-t', '--types', action='append', type=check_type,
                             help='Specify the advanced type combination to use '
                             'when running FLITSR. Note that this argument '
                             'overrides any of the individual advanced type '
                             'arguments given to FLITSR (such as --multi, --sblf, etc.).'
                             'This argument may be specified multiple times to add '
                             'multiple type combinations to run. The format for '
                             'this argument is: "--types <type>[+<type>...]", '
                             'where each <type> is a (case-insensitive) FLITSR '
                             f'advanced type. Allowed types are: {adv_types}')
        parser.add_argument('--no-override', action='store_true',
                            help='By default FLITSR will override the output '
                            'file(s) if they already exist, printing a warning '
                            'message. This option instead allows FLITSR to leave '
                            'output files that already exist, skipping that '
                            'output and continuing with the rest of the outputs '
                            '(if any)')
        parser.add_argument('-d', '--decimals', action='store', type=int,
                default=2, help='Sets the precision (number of decimal points) for '
                'the output of all of the calculations (default: %(default)s)')

        # Advanced types options
        primitives = (bool, str, int, float, Path)
        clusters = parser.add_argument_group('Clustering techniques',
            'One of the following clustering techniques may be specified, '
            'along with it\'s options')
        cluster_mu = clusters.add_mutually_exclusive_group()
        cluster_enum = advanced.ClusterType

        rankers = parser.add_argument_group('Ranking techniques',
            'One of the following advanced ranking techniques may be '
            'specified, along with it\'s options')
        ranker_mu = rankers.add_mutually_exclusive_group()
        ranker_enum = advanced.RankerType

        advanced_groups = [('cluster', cluster_enum, clusters, cluster_mu),
                           ('ranker', ranker_enum, rankers, ranker_mu)]

        for adv_name, adv_enum, group, mu in advanced_groups:
            for type_ in list(adv_enum):
                name, class_ = type_.name, type_.value
                disp_name = name.lower()
                help_ = '(default: %(default)s)'
                # add docstring
                if (class_.__doc__ is not None and class_.__doc__ != ''):
                    help_ = class_.__doc__ + ' ' + help_
                mu.add_argument('--'+disp_name, dest=adv_name,
                                action='store_const', const=adv_enum[name],
                                help=help_)
                argspec = inspect.getfullargspec(class_.__init__)
                def_diff = (len(argspec.args)-1) - (0 if
                                                    argspec.defaults is None
                                                    else len(argspec.defaults))
                for p_index, param in enumerate(argspec.args[1:]):
                    paramName = '--'+disp_name+'-'+param.replace('_', '-')
                    parser_args = {'help': '(default %(default)s)'}
                    # add default arguments
                    if (argspec.defaults is not None and p_index >= def_diff):
                        parser_args['default'] = argspec.defaults[p_index-def_diff]
                    # add choices
                    if (hasattr(class_, f'_{param}_opts')):
                        parser_args['choices'] = getattr(class_, f'_{param}_opts')
                    # add types
                    if (param in argspec.annotations):
                        paramType = argspec.annotations[param]
                        if (paramType is bool):
                            if ('default' in parser_args):
                                # check if default is True
                                if (parser_args['default']):
                                    parser_args['dest'] = disp_name+'_'+param
                                    paramName = ('--' + disp_name + '-no-' +
                                                 param.replace('_', '-'))
                                    parser_args['action'] = 'store_false'
                                else:
                                    parser_args['action'] = 'store_true'
                            else:
                                parser_args['action'] = 'store_true'
                        else:
                            if (paramType not in primitives):
                                if (not hasattr(class_, f'_{param}')):
                                    err = ('Could not find type conversion '
                                           f'for {param} in {name}')
                                    raise NameError(err)
                                paramType = getattr(class_, f'_{param}')
                            parser_args['type'] = paramType
                            if ('choices' not in parser_args):
                                parser_args['metavar'] = param
                    # finalize option
                    group.add_argument(paramName, **parser_args)  # type:ignore

        # manually set flitsr as the default
        parser.set_defaults(ranker=advanced.RankerType['FLITSR'])

        # parser.add_argument('--multi', action='store_true',
        #         help='Runs the FLITSR* (i.e. multi-round) algorithm')
        # parser.add_argument('-i', '--internal-ranking', action='store',
        #         choices=['flitsr', 'reverse', 'original', 'auto', 'conf'], default='auto',
        #         help='Specify the order in which the elements of each FLITSR basis '
        #         'are ranked. "flitsr" uses the order that FLITSR returns the basis '
        #         'in (i.e. from FLITSRs lowest to highest recursion depth), which '
        #         'aligns with FLITSRs confidence for each element being a fault. '
        #         '"reverse" uses the reverse of "flitsr" (i.e. the order in which '
        #         'FLITSR identifies the elements) which gives elements that use a '
        #         'larger part of the original test suite first. "original" returns '
        #         'the elements based on their original positions in the ranking '
        #         'produced by the base SBFL metric used by FLITSR.')

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

        # check type of general weffort
        def check_fault_type(nth):
            if (int(nth) > 0):
                return int(nth)
            else:
                raise argparse.ArgumentTypeError(f'Invalid fault number {nth}')

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
        calc_grp.add_argument('--weffort', dest='weff', action='append', metavar='N',
                type=check_fault_type, help='Display the wasted effort to the Nth fault')

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

        # Fault output options
        calc_grp.add_argument('--fault-num', dest='faults', action='append_const',
                              const='num', default=[],
                              help='Display the number of faults in the program')
        calc_grp.add_argument('--fault-ids', dest='faults', action='append_const',
                              const='ids',
                              help='Display the IDs of the faults in the program')
        calc_grp.add_argument('--fault-elems', dest='faults',
                              action='append_const', const='elems',
                              help='Display the elements that are faulty in the program')
        calc_grp.add_argument('--fault-all', dest='faults', action='append_const',
                              const='all',
                              help='Display all info of the faults in the program')

        # parser.add_argument('-p', '--parallel', action='store',
        #          choices=parallel_opts, metavar='ALGORITHM',
        #          help='Run one of the parallel debugging algorithms on the spectrum '
        #          'to produce multiple spectrums, and process all other options on '
        #          'each spectrum. Allowed values are: ['+', '.join(parallel_opts)+']')

        # parser.add_argument('--artemis', action='store_true',
        #                     help='Run the ARTEMIS technique on the spectrum to '
        #                     'produce the ranked lists. This option may be '
        #                     'combined with FLITSR and parallel to produce a '
        #                     'hybrid technique.')

        # TODO: Add OBA and worst args if necessary
        cut_eval_opts=['worst', 'best', 'resolve']
        parser.add_argument('--cutoff-eval', action='store', metavar='MODE',
                choices=cut_eval_opts, help='Specifies the performance mode to use '
                'when using a multi-fault fixing cut-off strategy to produce '
                'rankings. Allowed values are: ['+', '.join(cut_eval_opts)+']'+
                ' (default %(default)s)', default='worst')
        cutoff_opts = cutoff_points.getNames()
        parser.add_argument('--cutoff-strategy', action='store', metavar='STRATEGY',
                help='Cuts off the ranking using the given '
                'strategy\'s cut-off point. This affects both the rank output '
                'method and any calculations. Allowed values are: ['+
                ', '.join(cutoff_opts)+'] (default %(default)s). '
                'For basis, an optional value n may be given (e.g. basis=n) '
                'that determines the number of bases included before the cutoff')

        argcomplete.autocomplete(parser)

        args = parser.parse_args(argv)
        # Set the metrics based on 'all' or the default metric
        if (args.metrics is None):
            if (args.all is True):
                args.metrics = Suspicious.getNames()
            else:
                args.metrics = [default_metric]
        # Set the flitsr types based on 'all' or what is set
        if (args.all is True):
            if (args.types is None):
                args.types = [Config(), Config(advanced.RankerType['FLITSR']),
                              Config(advanced.RankerType['MULTI'])]
            if (len(args.weff) == 0 and len(args.top1) == 0 and
                    len(args.perc_at_n) == 0 and len(args.prec_rec) == 0):
                args.weff = ["first", "avg", "med", "last", 2, 3, 5]
                args.perc_at_n = ["perc"]
                args.prec_rec = [('p', 1), ('p', 5), ('p', 10), ('p', "f"),
                                 ('r', 1), ('r', 5), ('r', 10), ('r', "f")]
                args.faults = ["num"]
        elif (args.types is None):
            args.types = [Config(args.ranker, args.cluster)]
        # Check the input file type and set input method
        if (osp.isfile(args.input)):
            args.input_type = InputType.TCM
        elif (osp.isdir(args.input) and
                osp.isfile(osp.join(args.input, "matrix.txt"))):
            args.input_type = InputType.GZOLTAR
        else:
            parser.error("Input file type not supported")
        if (args.cutoff_strategy and args.cutoff_strategy.startswith('basis')):
            args.sbfl = False
            args.multi = 1
        self._add_params(args)
        return self

    def get_arg_group(self, group_name):
        group = {}
        prefix = group_name.lower()+'_'
        arg_dict = vars(self)
        for key in arg_dict:
            if (key.startswith(prefix)):
                group[key.removeprefix(prefix)] = arg_dict[key]
        return group


if __name__ == "__main__":
    args = Args().parse_args(sys.argv[1:])
    print(args)
