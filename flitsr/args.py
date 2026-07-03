from __future__ import annotations
import argparse
from argparse import ArgumentTypeError, Action
import argcomplete
import inspect
import sys
import re
from warnings import warn
from pathlib import Path
from os import path as osp
from typing import List, Dict, Any, Optional, IO, BinaryIO, Tuple, Set, \
        Union, Generic, Type, Iterator, Iterable, overload
from collections.abc import Callable
from flitsr.suspicious import Suspicious
from flitsr import cutoff_points
from flitsr.singleton import SingletonMeta
from flitsr.ranking import Tiebrk
from flitsr import advanced
from flitsr.advanced import Config
from flitsr.input.duplicates import DuplicateStrategy
from flitsr.calculations import BUModel, calcs_base


class _ParameterParser(Iterable[Tuple[str, Optional[Dict[str, Any]]]]):
    def __init__(self, fn: Callable, class_: Optional[Type[Any]] = None,
                 ext_name: Optional[str] = None,
                 include_existing: bool = False):
        """
        Constructs an iterable object that supports parsing of the parameters
        of the given function/method `fn` to be used in the command-line
        interface.

        Args:
          fn: The function/method to parse the parameters for. This should be
            a flitsr extension method, which contains dunder variables (e.g.
            "__choices__") added to the method by flitsr annotations for extra
            information.
          class_: (Optionally) the class of the method to parse the parameters
            for. This is only used for getting the type conversion functions
            which may be shared between multiple methods in the class.
          option_name: The name of the extension for this function/method that
            is to be added to the command-line interface. When not given, the
            name of the method/function will be used.
        """
        # if the class is provided, make sure we have the method (not function)
        if (class_ is not None and hasattr(class_, fn.__name__) and
                getattr(class_, fn.__name__) == fn):
            self.fn = getattr(object.__new__(class_), fn.__name__)
        else:
            self.fn = fn
        self.fn = inspect.unwrap(self.fn)
        self.ismethod = inspect.ismethod(self.fn)
        if (ext_name is None):
            self.name = self.fn.__name__
        else:
            self.name = ext_name
        self._argspec = inspect.getfullargspec(self.fn)
        if (self._argspec.defaults is None):
            num_defaults = 0
        else:
            num_defaults = len(self._argspec.defaults)
        num_args = len(self._argspec.args)
        if (self.ismethod):
            num_args -= 1
        self._def_diff = (num_args - num_defaults)
        self.class_ = class_
        self.params: List[str] = self._argspec.args
        if (self.ismethod):
            self.params = self.params[1:]
        self._p_index: int = 0
        self.num_params = len(self.params)
        self._include_existing = include_existing

    # global list of primitive types
    _primitives = (bool, str, int, float, Path)

    @staticmethod
    def _get_base_type(typ: Type[Any]) -> List[Type[Any]]:
        """ function to extract the base type from a typing.Union, etc."""
        if (hasattr(typ, '__origin__')):
            if (typ.__origin__ is Union):
                ret = list(typ.__args__)
                # remove NoneType from Optionals
                if (type(None) in ret):
                    ret.remove(type(None))
                return ret
            elif (typ.__origin__ is Generic):
                return [typ.__args__[0]]
        return [typ]

    def _gen_parameter(self, param: str, p_index: int) -> Dict[str, Any]:
        """
        Collect the information for a parameter from a flitsr extension method
        to be added to the flitsr command-line interface.

        Args:
          param: The parameter to process command-line arguments for.
          p_index: The index of the parameter in the method's parameter list.

        Returns:
          A dictionary containing all the information relating to the given
          parameter. The dictionary is in a format compatible with the
          parameters for the `argparse.ArgumentParser.add_argument` method.
        """
        parser_args: Dict[str, Any] = {}
        # get the parameter type(s) (if any)
        paramTypes = (self._get_base_type(self._argspec.annotations[param])
                      if param in self._argspec.annotations else None)
        # add default arguments if param has
        if (self._argspec.defaults is not None and p_index >= self._def_diff):
            parser_args['default'] = self._argspec.defaults[p_index -
                                                            self._def_diff]
            parser_args['help'] = '(default: %(default)s)'
        # else add param as conditionally "required" if not bool
        elif (paramTypes is None or paramTypes != [bool]):
            parser_args['help'] = '(required)'
            parser_args['required'] = True
        # add choices
        if (hasattr(self.fn, '__choices__') and
                param in self.fn.__choices__):
            parser_args['choices'] = self.fn.__choices__[param]
            parser_args['help'] = (f'Choices: {parser_args["choices"]} '
                                   + parser_args['help'])
        # add types
        if (paramTypes is not None):
            # function to deal with non-primitives
            def get_type_conv(name: str, param: str) -> Optional[Any]:
                if (hasattr(self.class_, f'_{param}')):
                    return getattr(self.class_, f'_{param}')
                elif (hasattr(self.fn, '__types__') and
                      param in self.fn.__types__):
                    return getattr(self.fn, '__types__')[param]
                else:
                    return None

            # only add automatic type conversion for single types
            if (len(paramTypes) == 1):
                paramType = paramTypes[0]
                type_conv = get_type_conv(self.name, param)
                if (type_conv is not None):
                    paramType = type_conv
                    parser_args['type'] = paramType
                    parser_args['metavar'] = param
                # specially handle bools
                elif (paramType is bool):
                    if ('default' in parser_args):
                        # check if default is True
                        if (parser_args['default']):
                            parser_args['action'] = 'store_false'
                        else:
                            parser_args['action'] = 'store_true'
                    else:
                        parser_args['action'] = 'store_true'
                # specially handle file IO types
                elif (inspect.isclass(paramType) and
                      issubclass(paramType, IO)):
                    if (issubclass(paramType, BinaryIO)):
                        parser_args['type'] = argparse.FileType('rb')
                    else:
                        parser_args['type'] = \
                          argparse.FileType('r', encoding='UTF-8')
                elif (paramType in _ParameterParser._primitives):
                    parser_args['type'] = paramType
                    parser_args['metavar'] = param
                else:
                    err = ('Could not find type conversion '
                           f'for {param} in {self.name}')
                    raise NameError(err)
            # deal with multiple parameter types
            else:
                type_conv = get_type_conv(self.name, param)
                if (type_conv is None):
                    err = ('Could not find type conversion '
                           f'for {param} in {self.name}')
                    raise NameError(err)
                parser_args['type'] = type_conv
                parser_args['metavar'] = param
        return parser_args

    def __iter__(self) -> Iterator[Tuple[str, Optional[Dict[str, Any]]]]:
        self._p_index = 0
        return self

    def __next__(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        existing = False
        try:
            param = self.params[self._p_index]
            if (self._include_existing):
                if (hasattr(self.fn, '__existing__') and
                        param in self.fn.__existing__):
                    existing = True
            elif (hasattr(self.fn, '__existing__')):
                while (param in self.fn.__existing__):
                    self._p_index += 1
                    param = self.params[self._p_index]
        except IndexError:
            raise StopIteration
        parser_args = None
        if (not existing):
            parser_args = self._gen_parameter(param, self._p_index)
        self._p_index += 1
        assert ((parser_args is None) == (existing and self._include_existing))
        return param, parser_args


class Args(argparse.Namespace, metaclass=SingletonMeta):
    """
    The global Singleton holding the specified/default arguments used across
    the flitsr framework.
    """
    def __init__(self, argv: Optional[List[str]] = None,
                 cmd_line: bool = False, noparse: bool = False):
        """
        Initialize the Args Singleton object. Note that this constructor is
        only ever called once for each program run. Other attempts to construct
        this object will return the pre-existing ``Args`` Singleton object.

        Args:
          argv: Optional[List[str]]: The optional list of command line
              arguments to parse. If not given and the Args object is set to
              read from the command line (see ``cmd_line``), sys.argv is used
              instead.
          cmd_line: bool: Whether to parse arguments given in command-line
              style. When True, Args will either parse the arguments given in
              ``argv``, or ``sys.argv`` if ``argv`` is ``None``. If False,
              ``Args`` will just load the default values for each command line
              option, and ignore required arguments. (Default value = False)
          noparse: bool: When True, this ``Args`` object will not attempt to
              parse any arguments. This is primarily used for generating
              documentation for flitsr's command line. (Default value = False)
        """
        self._deprecations: Dict[str, str] = {}
        self._default_metric = 'ochiai'
        self._adv_required_args: Dict[str, Tuple[str, Set[str]]] = dict()
        self._advanced_params: Dict[str, Dict[str, Any]] = {}
        self._parser = self._gen_parser(cmd_line)
        if (not noparse):
            self._parse_args(argv)

    def _add_params(self, params: argparse.Namespace) -> None:
        dict_ = vars(params)
        for key in dict_:
            setattr(self, key, dict_[key])

    @staticmethod
    def _check_file(filename: str) -> str:
        """ Check file exists function """
        if (osp.exists(filename)):
            return filename
        else:
            raise ArgumentTypeError('Could not find input file: '
                                    f'\"{filename}\"')

    def _check_type(self, type_comb: str) -> Config:
        """ check FLITSR type combinations function """
        type_sep = type_comb.split('+')
        cluster = None
        ranker = None
        refiner = None
        args: Dict[str, Dict[str, Any]] = {}
        for t in type_sep:
            m = re.fullmatch("([^(]+)(?:\\(([^)]+)\\))?", t)
            if (m is None):
                raise ArgumentTypeError('Invalid type for --all-types: '
                                        f'\"{t}\"')
            t = m.group(1).upper()
            if (hasattr(advanced.ClusterType, t)):
                if (cluster is not None):
                    raise ArgumentTypeError('Cannot have two cluster types: '
                                            f'{cluster.name} and {t}')
                cluster = advanced.ClusterType[t]
            elif (hasattr(advanced.RefinerType, t)):
                if (refiner is not None):
                    raise ArgumentTypeError('Cannot have two refiner types: '
                                            f'{refiner.name} and {t}')
                refiner = advanced.RefinerType[t]
            elif (hasattr(advanced.RankerType, t)):
                if (ranker is not None):
                    raise ArgumentTypeError('Cannot have two ranker types: '
                                            f'{ranker.name} and {t}')
                ranker = advanced.RankerType[t]
            else:
                raise ArgumentTypeError('Invalid type for --all-types: '
                                        f'\"{t}\"')
            if (m.group(2) is None):
                params = {}
            else:
                params = dict(re.findall("([^=,]+)=['\"]?([^,'\"]+)['\"]?",
                                         m.group(2)))
                # check params are valid and convert types
                for k, v in params.items():
                    # check valid param
                    if (k not in self._advanced_params[t]):
                        raise ArgumentTypeError('Invalid parameter '
                                                f'\"{k}\" for type {t}')
                    else:
                        # convert type
                        try:
                            converted = self._advanced_params[t][k](v)
                            params[k] = converted
                        except Exception:
                            raise ArgumentTypeError('Invalid value '
                                f'\"{v}\" for parameter {k} of type {t}')
            args[t] = params
        adv_type = Config(ranker, cluster, refiner, args)
        return adv_type

    @staticmethod
    def _type_bundler(function: Callable[[str], Any],
                      *functions: Callable[[str], Any]) \
            -> Union[Callable[[str], Any], Callable[[List[str]], List[Any]]]:
        if (len(functions) == 0):
            return function
        else:
            all_functions = [function, *functions]

            def bundler(lst: List[str]) -> List[Any]:
                ret = []
                for i in range(len(all_functions)):
                    try:
                        ret.append(all_functions[i](lst[i]))
                    except (TypeError, ValueError, ArgumentTypeError) as e:
                        if (len(e.args) > 0):
                            updated_args = (f'argument {i+1}: '+e.args[0],
                                            *e.args[1:])
                        else:
                            updated_args = (f'argument {i+1}',)
                        raise ValueError(*updated_args)
                return ret
            return bundler

    @overload
    @staticmethod
    def _bundler_action(bundler: Callable[[str], Any], ids: str, name:
                        Optional[str] = None) -> Type[Action]: ...

    @overload
    @staticmethod
    def _bundler_action(bundler: Callable[[List[str]], List[Any]], ids:
                        List[str], name: Optional[str] =
                        None) -> Type[Action]: ...

    @overload
    @staticmethod
    def _bundler_action(bundler: None, ids: None, name:
                        Optional[str] = None) -> Type[Action]: ...

    @staticmethod
    def _bundler_action(bundler: Union[None, Callable[[str], Any],
                        Callable[[List[str]], List[Any]]], ids: Union[None,
                        str, List[str]],
                        name: Optional[str] = None) -> Type[Action]:
        class BundlerAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                args: Union[Any, Dict[str, Any]]
                if (bundler is None or ids is None):
                    args = None
                else:
                    try:
                        typed_values = bundler(values)
                    except (TypeError, ValueError, ArgumentTypeError) as e:
                        raise argparse.ArgumentError(self, str(e))
                    args = {}
                    if (isinstance(ids, str)):
                        args[ids] = typed_values
                    else:
                        for i, id_ in enumerate(ids):
                            args[id_] = typed_values[i]
                if (name is None):
                    setattr(namespace, self.dest, args)
                else:
                    if (not hasattr(namespace, self.dest) or
                            getattr(namespace, self.dest) is None):
                        setattr(namespace, self.dest, dict())
                    d = getattr(namespace, self.dest)
                    d.setdefault(name, list()).append(args)
        return BundlerAction

    @staticmethod
    def _boolConv(x: str) -> bool:
        if (x not in ['True', 'False']):
            raise ValueError('invalid literal for '
                             f'bool: \'{x}\'')
        return x == 'True'

    def _gen_parser(self, cmd_line: bool = True) -> argparse.ArgumentParser:
        """
        Generate the ArgumentParser that will be used to parse arguments.
        This function is used by the ``parse_args`` function, as well as to
        initialize the Args object and generate documentation. Setting
        ``cmd_line`` to False will disable required arguments, allowing the
        default values to be retrived.

        Args:
          cmd_line: bool: Whether to generate the parser for the command line,
              or just for the default arguments. (Default value = True)

        Returns:
            The argparse ArgumentParser that was generated.
        """
        # General options
        parser = argparse.ArgumentParser(prog='flitsr', description='An automatic '
                'fault finding/localization tool for multiple faults.')
        if (cmd_line):
            parser.add_argument('input', type=Args._check_file,
                                help='The coverage file (TCM) or directory '
                                '(GZoltar) containing the coverage collected '
                                'for the system over the test suite')
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
        metric_choices = (Suspicious.getNames(True) +
                          [m.lower() for m in advanced.all_types.keys()])
        parser.add_argument('-m', '--metric', dest='metrics', action='append',
                choices=metric_choices, metavar='METRIC',
                help='The underlying (SBFL) metric(s) to use when either ranking '
                '(if the sbfl option is given), or running the FLITSR algorithm. '
                'Option may be supplied multiple times to run multiple metrics. '
                'Specifying multiple metrics will output the results of each '
                'metric to a seperate file using the metric\'s name instead of '
                f'stdout. Allowed values are: [{", ".join(Suspicious.getNames(True))}] '
                f'(default: {self._default_metric}). When using the FLITSR '
                'advanced technique (or similar), you may also specify '
                'an advanced technique here to use as base metric, in which '
                'case the --flitsr-default_metric option may be used to '
                'likewise specify the base metric for that advanced '
                'technique. Note that it is your job to determine whether the '
                'given advanced technique is compatible with the FLITSR (or '
                'similar) algorithm, as this is not ensured for all advanced '
                'types.')
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
        parser.add_argument('--duplicates', default=DuplicateStrategy.REFUSE,
                choices=list(DuplicateStrategy),
                type=DuplicateStrategy.from_string,
                help='Specify the strategy for dealing with duplicate '
                'elements in the spectrum. ALLOW: Allow the spectrum to '
                'contain duplicates, which will then use a random index to '
                'distinguish them. IGNORE: Silently remove and ignore '
                'duplicate elements in the spectrum, merging their spectra. '
                'REFUSE: Raise an exception if any duplicate elements are '
                'encountered when reading in the spectrum.')
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
        parser.add_argument('-t', '--types', action='append', type=self._check_type,
                             help='Specify the advanced type combination to use '
                             'when running FLITSR. Note that this argument '
                             'overrides any of the individual advanced type '
                             'arguments given to FLITSR (such as --multi, --sblf, etc.).'
                             'This argument may be specified multiple times to add '
                             'multiple type combinations to run. The format for '
                             'this argument is: "--types <type>[+<type>...]", '
                             'where each <type> is a (case-insensitive) FLITSR '
                             f'advanced type. Allowed types are: {adv_types}')
        parser.add_argument('-p', '--print-params', nargs='?', const="",
                            default=None, type=str, metavar='FORMAT_STR',
                            help='When producing multiple output files, '
                            'specifies that the parameters for advanced types,'
                            'given by the --types option, should be included '
                            'in the names of these output files. Without an '
                            'argument, this option produces file names with '
                            'advanced type parameters of the form "{k}-{v}" '
                            'where {k} is the parameter name, and {v} is the '
                            'value. Other formats can be constructed by '
                            'instead providing an argument using the same '
                            '"{k}", "{v}" syntax.')
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
        advanced_groups: List[Tuple[str, Any, Any, Any]] = []

        refiner_enum = advanced.RefinerType
        if (len(refiner_enum) != 0):
            refiners = parser.add_argument_group('Spectrum refiner techniques',
                'One of the following spectrum refining techniques may be '
                'specified, along with it\'s options')
            refiner_mu = refiners.add_mutually_exclusive_group()
            advanced_groups.append(('refiner', refiner_enum, refiners,
                                    refiner_mu))

        cluster_enum = advanced.ClusterType
        if (len(cluster_enum) != 0):
            clusters = parser.add_argument_group('Clustering techniques',
                'One of the following clustering techniques may be specified, '
                'along with it\'s options')
            cluster_mu = clusters.add_mutually_exclusive_group()
            advanced_groups.append(('cluster', cluster_enum, clusters,
                                    cluster_mu))

        ranker_enum = advanced.RankerType
        if (len(ranker_enum) != 0):
            rankers = parser.add_argument_group('Ranking techniques',
                'One of the following advanced ranking techniques may be '
                'specified, along with it\'s options (default: flitsr)')
            ranker_mu = rankers.add_mutually_exclusive_group()
            advanced_groups.append(('ranker', ranker_enum, rankers, ranker_mu))

        for adv_name, adv_enum, group, mu in advanced_groups:
            for type_ in list(adv_enum):
                name, class_ = type_.name, type_.value
                init = class_.__init__
                disp_name = name.lower()
                help_ = ''  # '(default: %(default)s)'
                # add docstring
                if (class_.__doc__ is not None and class_.__doc__ != ''):
                    help_ = (re.sub("\\s+", " ", class_.__doc__.strip()) +
                             ' ' + help_)
                # add cmd line argument for this advanced type
                mu.add_argument('--'+disp_name, dest=adv_name,
                                action='store_const', const=adv_enum[name],
                                help=help_)
                # add cmd-line arguments for each parameter of this adv type
                pp = _ParameterParser(init, class_, ext_name=name,
                                      include_existing=True)
                parser_args: Optional[Dict[str, Any]]
                self._advanced_params[name] = dict()
                for (param, parser_args) in pp:
                    self._advanced_params[name][param] = None
                    # skip adding this parameter if it is marked as existing
                    if (parser_args is None):
                        continue
                    paramName = '--'+disp_name+'-'+param.replace('_', '-')
                    # check if argument is required
                    if (parser_args.get('required', False) is True):
                        # remove the required parser argument
                        parser_args.pop('required', None)
                        # add to the list of potentially required args
                        if (name not in self._adv_required_args):
                            self._adv_required_args[name] = (adv_name, set())
                        self._adv_required_args[name][1].add(param)
                    # specially handle boolean options with default True
                    if (parser_args.get('action', '') == 'store_false'):
                        parser_args['dest'] = disp_name+'_'+param
                        paramName = ('--' + disp_name + '-no-' +
                                     param.replace('_', '-'))
                    # store parser type converter
                    if ('type' in parser_args):  # must be non-bool type
                        self._advanced_params[name][param] = parser_args['type']
                    else:  # must be bool type
                        self._advanced_params[name][param] = Args._boolConv
                    # finalize option
                    group.add_argument(paramName, **parser_args)

        parser.add_argument('-bu', '--bug-understanding', metavar='MODEL',
                            default=BUModel.PERFECT, type=BUModel.from_string,
                            choices=BUModel.get_types(),
                            help='Specify the bug understanding model to use '
                            'when evaluating the rankings using any of the '
                            'calculations. The bug understanding model is the '
                            'number of locations that must be inspected for '
                            'each fault in order to identify that fault. The '
                            'default is "perfect" bug understanding, i.e., '
                            'where it is only necessary to inspect a single '
                            'fault location to identify a fault. Inept bug '
                            'understanding instead specifies that all fault '
                            'locations must be inspected to localize a fault. '
                            'Finally, imperfect is when only some (by default '
                            'half) of the locations must be inspected. '
                            f'Choices: {BUModel.get_types()}')

        # Tie breaking options
        tie_grp = parser.add_argument_group('Tie breaking strategy',
                                            'Specifies the tie breaking '
                                            'strategy to use for FLITSR and '
                                            'the localization')
        tie_grp.add_argument('--tiebrk', action='store_const',
                             default=Tiebrk.ORIG, const=Tiebrk.EXEC,
                             help='Breaks ties using only execution counts')
        tie_grp.add_argument('--rndm', action='store_const', const=Tiebrk.RNDM,
                             dest='tiebrk', help='Breaks ties by a randomly '
                             'ordering')
        tie_grp.add_argument('--otie', action='store_const', const=Tiebrk.ORIG,
                             dest='tiebrk', help='Breaks ties by using the '
                             'original base metric ranking (in the case of '
                             'FLITSR) and by execution counts otherwise')

        # Calculation options
        calc_grp = parser.add_argument_group('Calculations',
                'The following arguments replace the default ranking output of '
                'FLITSR with evaluation calculations. Multiple of the following '
                'arguments can be given in the same call')

        for calc_name, calc_fn in calcs_base.items():
            # initialize argparse args
            argument_args: Dict[str, Any] = {'metavar': [], 'nargs': 0,
                                             'dest': 'calcs'}
            argument_names = {f'--{calc_name}'}
            help_ = ''
            if (hasattr(calc_fn, '__doc__')):
                argument_args['help'] = getattr(calc_fn, '__doc__')
            if (hasattr(calc_fn, '__arg_names__')):
                for arg_name in getattr(calc_fn, '__arg_names__'):
                    if (len(arg_name) == 1):
                        argument_names.add(f'-{arg_name}')
                    elif (arg_name.startswith('-')):
                        argument_names.add(arg_name)
                    else:
                        argument_names.add(f'--{arg_name}')
            # parse the parameters
            pp = _ParameterParser(calc_fn)
            type_funcs = []
            for param, parser_args in pp:
                assert (parser_args is not None)
                argument_args['metavar'].append(param)
                argument_args['nargs'] += 1
                # print(calc_name, param, parser_args)
                if (parser_args.get('required', False) is True):
                    if ('type' in parser_args):
                        type_funcs.append(parser_args['type'])
                    else:
                        type_funcs.append(str)
                elif ('action' in parser_args and
                      parser_args['action'] in ['store_true', 'store_false']):
                    type_funcs.append(Args._boolConv)

            if (len(argument_args['metavar']) == 0):
                argument_args['action'] = Args._bundler_action(None, None,
                                                               calc_name)
                # Do not add empty metavar
                del argument_args['metavar']
            else:
                tb = Args._type_bundler(type_funcs[0], *type_funcs[1:])
                if (len(argument_args['metavar']) == 1):
                    ids = argument_args['metavar'][0]
                    argument_args['nargs'] = None
                else:
                    ids = argument_args['metavar']
                argument_args['action'] = Args._bundler_action(tb, ids,
                                                               calc_name)
                argument_args['metavar'] = tuple(argument_args['metavar'])
            # sort argument names by length and then alphabetical
            def sort_len_alph(s): return (len(s), s.lower())
            # print(sorted(argument_names, key=sort_len_alph), argument_args,
            #       type_funcs)
            calc_grp.add_argument(*sorted(argument_names, key=sort_len_alph),
                                  **argument_args)

        self._deprecations['--one-top1'] = ('`--one-top1` is deprecated and '
                                            'will be removed in an upcomming '
                                            'release. Use `--one-top` instead')
        self._deprecations['--all-top1'] = ('`--all-top1` is deprecated and '
                                            'will be removed in an upcomming '
                                            'release. Use `--all-top` instead')
        self._deprecations['--perc-top1'] = ('`--perc-top1` is deprecated and '
                                             'will be removed in an upcomming '
                                             'release. Use `--perc-top` instead')

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
        return parser

    def _parse_args(self, argv: Optional[List[str]] = None) -> Args:
        """
        Parse the arguments defined by args for the flitsr program with
        python's argparse. The result is an argparse Namespace object which
        includes all of the arguments parsed (or default values).

        Args:
          argv: Optional[List[str]]: (Default value = None) The list of
              arguments to parse, usual taken from the command line arguments
              given

        Returns:
          The constructed Args object
        """

        args = self._parser.parse_args(argv)

        # check for deprecations
        for dep, message in self._deprecations.items():
            if ((argv is not None and dep in argv) or
                    (argv is None and dep in sys.argv)):
                # stacklevel=10 to remove all context
                warn(message, category=FutureWarning, stacklevel=10)

        # manually set flitsr as the default
        default_ranker_used = False
        if (not hasattr(args, 'ranker') or args.ranker is None):
            args.ranker = advanced.RankerType['FLITSR']
            default_ranker_used = True

        # check "required" advanced type arguments
        for adv_name, (adv_type, adv_args) in self._adv_required_args.items():
            if (getattr(args, adv_type) is not None and
                getattr(args, adv_type).name == adv_name):
                dname = adv_name.lower()
                for adv_arg in adv_args:
                    if (getattr(args, dname+'_'+adv_arg) is None):
                        err = (f'--{dname}-{adv_arg} is required when '
                               f'--{dname} is used')
                        self._parser.error(err)
        # Set the metrics based on 'all' or the default metric
        if (args.metrics is None):
            if (args.all is True):
                args.metrics = Suspicious.getNames()
            else:
                args.metrics = [self._default_metric]
        # Set the flitsr types based on 'all' or what is set
        if (args.all is True):
            if (args.types is None):
                ts = {}
                if (getattr(args, 'refiner', None) is not None):
                    ts['refiner'] = args.refiner
                if (getattr(args, 'cluster', None) is not None):
                    ts['cluster'] = args.cluster
                if (getattr(args, 'ranker', None) is not None and
                    not default_ranker_used):
                    ts['ranker'] = args.ranker
                    args.types = [Config(**ts)]
                else:
                    args.types = [Config(**ts),
                                  Config(advanced.RankerType['FLITSR'], **ts),
                                  Config(advanced.RankerType['MULTI'], **ts)]
            if (args.calcs is None or len(args.calcs) == 0):
                args.calcs = {
                    "first": [{}],
                    "average": [{}],
                    "median": [{}],
                    "last": [{}],
                    "weffort": [{'n': 2}, {'n': 3}, {'n': 5}],
                    "perc@n": [{}],
                    "precision-at": [{'x': 1}, {'x': 5}, {'x': 10}, {'x': "f"}],
                    "recall-at": [{'x': 1}, {'x': 5}, {'x': 10}, {'x': "f"}],
                    "fault-num": [{}],
                    "all-top": [{'x': 1}, {'x': 5}, {'x': 10}],
                    "one-top": [{'x': 5}]
                    }
        elif (args.types is None):
            args.types = [Config(args.ranker, getattr(args, 'cluster', None),
                                 getattr(args, 'refiner', None))]
        if (args.cutoff_strategy and args.cutoff_strategy.startswith('basis')):
            args.sbfl = False
            args.multi = 1
        self._add_params(args)
        return self

    def get_arg_group(self, group_name: str) -> Dict[str, Any]:
        """
        Return the arguments for the given argument group.

        Args:
          group_name: The name of the argument group to get arguments for. For
              example, for the SBFL advanced type, the argument name would be
              "sbfl", and would return any arguments that SBFL needs.

        Returns:
          A dictionary with all the arguments in this group as key-value pairs.
          This can be used when calling a function that requires these
          arguments using python dictionary unpacking (e.g.
          ``function_to_call(**get_arg_group(...))``).
        """
        group = {}
        params = self._advanced_params[group_name.upper()]
        prefix = group_name.lower()+'_'
        for param in params:
            if (hasattr(self, prefix+param)):
                group[param] = getattr(self, prefix+param)
            elif (hasattr(self, param)):
                group[param] = getattr(self, param)
            elif (param == 'args'):  # special case for full args
                group[param] = self
            else:
                raise KeyError(f'Could not find {param} in args!')
        return group


def get_parser() -> argparse.ArgumentParser:
    """ Return the parser for ``flitsr``. Used for the documentation """
    return Args(cmd_line=True, noparse=True)._parser


if __name__ == "__main__":
    args = Args(sys.argv[1:], cmd_line=True)
    print(args)
