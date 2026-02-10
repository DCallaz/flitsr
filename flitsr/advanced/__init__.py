from __future__ import annotations
import pkgutil
from flitsr import advanced
from flitsr.advanced.refiner import Refiner
from flitsr.advanced.cluster import Cluster
from flitsr.advanced.ranker import Ranker
from enum import Enum
import importlib
from typing import Union, Optional, Any, Dict, Type, TYPE_CHECKING, overload
import sys
if TYPE_CHECKING:
    from flitsr.args import Args
from deprecated.sphinx import deprecated, versionadded, versionchanged

_rankers = {}
_clusters = {}
_refiners = {}
all_types = {}
all_types_print = []


def register_ranker(cls):
    if (cls.__name__.upper() in all_types):
        raise ValueError(f'Duplicate advanced types for name "{cls.__name__}"')
    _rankers[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_cluster(cls):
    if (cls.__name__.upper() in all_types):
        raise ValueError(f'Duplicate advanced types for name "{cls.__name__}"')
    _clusters[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_refiner(cls):
    if (cls.__name__.upper() in all_types):
        raise ValueError(f'Duplicate advanced types for name "{cls.__name__}"')
    _refiners[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


# load local advanced types
__all__ = [m[1] for m in pkgutil.iter_modules(advanced.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)
# load plugin advanced types
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points
adv_entry_points = entry_points(group='flitsr.advanced')
for adv_ep in adv_entry_points:
    adv_ep.load()

RefinerType = Enum('RefinerType', _refiners)  # type:ignore
# module=advanced, qualname='advanced.RefinerType')
ClusterType = Enum('ClusterType', _clusters)  # type:ignore
# module=advanced, qualname='advanced.ClusterType')
RankerType = Enum('RankerType', _rankers)  # type:ignore
# module=advanced, qualname='advanced.RankerType')

AdvType = Union[RefinerType, ClusterType, RankerType]

for cls in all_types.values():
    if (hasattr(cls, '__print_name__')):
        all_types_print.append(cls.__print_name__.lower())
    else:
        all_types_print.append(cls.__name__.lower())


@versionchanged(version='2.3.0', reason='Replaced the `ranker`, `cluster`, '
                'and `refiner` attributes with functions constructing them')
class Config:
    """
    The advanced type configuration for a particular run of SBFL methods.

    Optionally contains a single Refiner, Cluster, and/or Ranker, as well as
    any arguments related to these advanced types. Multiple of these Config
    objects can be created in the same execution.
    """
    @versionchanged(version='2.4.0',
                    reason='Added the `args` optional argument')
    def __init__(self, ranker: Optional[RankerType] = None,
                 cluster: Optional[ClusterType] = None,
                 refiner: Optional[RefinerType] = None,
                 args: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Construct a `Config` object with the given ranker, cluster, and/or
        refiner (all optional).

        Args:
          ranker:  The (optional) `RankerType` to include in this config
          cluster: The (optional) `ClusterType` to include in this config
          refiner: The (optional) `RefinerType` to include in this config
          args:    If given, the dictionary containing additional arguments for
            each of the advanced types. The dictionary is indexed by the name
            of the advanced type, with the value being another dictionary with
            argument names and values. For example: `{'MULTI': {'cutoff': 5}}`
            will set the `cutoff <flitsr.advanced.flitsr.Multi.__init__>`
            parameter of the `MULTI <flitsr.advanced.flitsr.Multi>` RankerType.
        """
        self._cluster = cluster
        self._ranker = ranker
        self._refiner = refiner
        if (args is None):
            self._args = {}
        else:
            self._args = args

    def __str__(self, params: Optional[str] = ""):
        return self.get_str(filename=True, params=params)

    @versionadded(version='2.4.0')
    def get_str(self, filename=False, params: Optional[str] = None):
        """
        Returns a string description of the advanced types of this config
        object that can be used either in the name of the output file
        (`filename=True`), or for other script use (`filename=False`).

        Args:
          params: (Default value = None) If and how to include
            advanced type parameters in the output string. If None,
            parameters will not be included in the output string. If the
            empty string ("") is given, parameters will be included in the
            format "{k}-{v}" (for filenames) or "{k}={v}" (for
            non-filenames), where "{k}" is the parameter name, and "{v}" the
            value. Alternatively, a different format can be specified by
            giving a string using the same "{k}", "{v}" format.

        Returns:
          A string description of this `Config`.
        """
        c = '_' if filename else '+'
        components = [self._ranker or RankerType['SBFL'], self._refiner,
                      self._cluster]
        string = c.join(self._get_adv_name(c, filename, params)
                        for c in components if c is not None)
        return string

    def _get_args(self, adv_type: AdvType):
        return self._args.get(adv_type.name.upper(), {})

    def _get_params(self, adv_type: AdvType, args: Args):
        arg_params = args.get_arg_group(adv_type.name)
        custom_params = self._get_args(adv_type)
        refiner_params = {**arg_params, **custom_params}
        return refiner_params

    @versionadded(version='2.4.0')
    def set_arg(self, adv_type: AdvType, arg_name: str, arg_value: Any):
        """
        Set the argument given by `arg_name` with `arg_value` for the given
        advanced type.

        Args:
          adv_type: The advanced type to set the argument for.
          arg_name: str: The name of the argument to set
          arg_value: `Any <typing.Any>`: The value of the argument to set
        """
        self._args.setdefault(adv_type.name, {})[arg_name] = arg_value

    @versionadded(version='2.4.0')
    def refiner(self, args: Args) -> Optional[Refiner]:
        """
        Build and return this `Config`'s `RefinerType`, if available.

        Args:
          args: The global flitsr arguments to use when constructing this
            `Config`'s `RefinerType`.

        Returns:
          This `Config`'s constructed `Refiner <flitsr.advanced.refiner.Refiner>`
          object, or `None` if no `RefinerType` has been set.
        """
        return self.build_adv_type(self._refiner, args)

    @versionadded(version='2.4.0')
    def cluster(self, args: Args) -> Optional[Cluster]:
        """
        Build and return this `Config`'s `ClusterType`, if available.

        Args:
          args: The global flitsr arguments to use when constructing this
            `Config`'s `ClusterType`.

        Returns:
          This `Config`'s constructed `Cluster <flitsr.advanced.cluster.Cluster>`
          object, or `None` if no `ClusterType` has been set.
        """
        return self.build_adv_type(self._cluster, args)

    @versionadded(version='2.4.0')
    def ranker(self, args: Args) -> Optional[Ranker]:
        """
        Build and return this `Config`'s `RankerType`, if available.

        Args:
          args: The global flitsr arguments to use when constructing this
            `Config`'s `RankerType`.

        Returns:
          This `Config`'s constructed `Ranker <flitsr.advanced.ranker.Ranker>`
          object, or `None` if no `RankerType` has been set.
        """
        return self.build_adv_type(self._ranker, args)

    @overload
    def build_adv_type(self, adv_type: RankerType, args: Args) -> Ranker: ...

    @overload
    def build_adv_type(self, adv_type: ClusterType, args: Args) -> Cluster: ...

    @overload
    def build_adv_type(self, adv_type: RefinerType, args: Args) -> Refiner: ...

    @overload
    def build_adv_type(self, adv_type: None, args: Args) -> None: ...

    @versionadded(version='2.4.0')
    def build_adv_type(self, adv_type: Optional[AdvType], args: Args) -> Union[
            Refiner, Cluster, Ranker, None]:
        """
        Constructs the advanced type given by `adv_type` using the parameters
        in both the given `args` and this `Config`'s arguments.

        Args:
          adv_type: The advanced type to construct, which is one of
            `RefinerType`, `ClusterType`, or `RankerType`.
          args: The global flitsr arguments to use when constructing the
            given advanced type.

        Returns:
          The constructed advanced type object, which corresponds to the given
          `adv_type` argument.
        """
        if (adv_type is None):
            return None
        params = self._get_params(adv_type, args)
        mthd = adv_type.value(**params)
        return mthd

    @versionadded(version='2.4.0')
    def get_concrete(self, adv_type: Union[Type[RefinerType],
                     Type[ClusterType], Type[RankerType]]) -> Optional[str]:
        """
        Returns a string name of this `Config`'s concrete advanced type for the
        given category (Refiner, Cluster or Ranker), if it is available.
        For example, if RankerType was given, and this Config contained the
        SBFL RankerType, then "SBFL" would be returned. If there is no concrete
        advanced type for the given category, None is returned.

        Args:
          adv_type: The advanced type category to retrieve.

        Returns:
          The name of the concrete implementation for the given advanced type
          in this `Config` object, or None if no concrete implementation is
          available.
        """
        typ: Optional[AdvType] = None
        if (adv_type is RefinerType):
            typ = self._refiner
        elif (adv_type is ClusterType):
            typ = self._cluster
        elif (adv_type is RankerType):
            typ = self._ranker
        if (typ is None):
            return None
        else:
            return typ.name

    def _get_adv_name(self, typ: AdvType, filename: bool,
                      params: Optional[str] = None) -> str:
        # first get args (if needed and available)
        args = self._get_args(typ)
        # Always add params for non-filename
        if (not filename and params is None):
            params = ""
        if (params is not None and args is not None and len(args) > 0):
            if (params == ""):
                if (filename):
                    params = "{k}-{v}"
                else:
                    params = "{k}={v}"
            param_set = []
            for k, v in args.items():
                if (filename):
                    k = k.replace("_", "-")
                param_set.append(params.replace("{k}", k)
                                       .replace("{v}", v))
            if (filename):
                a = '_' + '_'.join(param_set)
            else:
                a = '(' + ','.join(param_set) + ')'
        else:
            a = ''
        # then get name
        if (filename and hasattr(typ.value, '__print_name__')):
            name = typ.value.__print_name__.lower()
        elif (filename):
            name = typ.name.lower()
        else:
            name = typ.name.upper()
        return name + a

    @versionadded(version='2.4.0')
    def __repr__(self, params: Optional[str] = ""):
        return self.get_str(filename=False, params=params)

    @versionchanged(version='2.4.0',
                    reason='Added the `params` optional argument')
    def get_file_name(self, params: Optional[str] = None):
        """
        Synonym for `Config.get_str(filename=True, ...) <get_str>`.

        Returns a string description of the advanced types of this config
        object that can be used in the name of the output file.

        Args:
          params: (Default value = None) Whether to include advanced type
            parameters in the file name. See the `get_str` method for a
            description of the format.

        Returns:
          A string description of this `Config` for filename use.
        """
        return self.get_str(filename=True, params=params)
