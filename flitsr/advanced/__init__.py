from __future__ import annotations
import pkgutil
from flitsr import advanced
from enum import Enum
import importlib
from typing import Union, Optional, Any, Dict, Type, TYPE_CHECKING
import sys
if TYPE_CHECKING:
    from flitsr.args import Args

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

RefinerType = Enum('RefinerType', _refiners,  # type:ignore
                   module=advanced, qualname='advanced.RefinerType')
ClusterType = Enum('ClusterType', _clusters,  # type:ignore
                   module=advanced, qualname='advanced.ClusterType')
RankerType = Enum('RankerType', _rankers,  # type:ignore
                  module=advanced, qualname='advanced.RankerType')

AdvType = Union[RefinerType, ClusterType, RankerType]

for cls in all_types.values():
    if (hasattr(cls, '__print_name__')):
        all_types_print.append(cls.__print_name__.lower())
    else:
        all_types_print.append(cls.__name__.lower())


class Config:
    def __init__(self, ranker: Optional[RankerType] = None,
                 cluster: Optional[ClusterType] = None,
                 refiner: Optional[RefinerType] = None,
                 args: Optional[Dict[str, Dict[str, Any]]] = None):
        self._cluster = cluster
        self._ranker = ranker
        self._refiner = refiner
        if (args is None):
            self._args = {}
        else:
            self._args = args

    def __str__(self):
        return self._get_str()

    def _get_str(self, printed=False):
        c = '_' if printed else '+'
        components = [self._ranker or RankerType['SBFL'], self._refiner,
                      self._cluster]
        string = c.join(self._get_name(c, printed) for c in components
                        if c is not None)
        return string

    def _get_args(self, adv_type: AdvType):
        return self._args.get(adv_type.name.upper(), {})

    def _get_params(self, adv_type: AdvType, args: Args):
        arg_params = args.get_arg_group(adv_type.name)
        custom_params = self._get_args(adv_type)
        refiner_params = {**arg_params, **custom_params}
        return refiner_params

    def set_arg(self, adv_type: AdvType, arg_name: str, arg_value: Any):
        self._args.setdefault(adv_type.name, {})[arg_name] = arg_value

    def refiner(self, args: Args):
        return self.run_adv_type(self._refiner, args)

    def cluster(self, args: Args):
        return self.run_adv_type(self._cluster, args)

    def ranker(self, args: Args):
        return self.run_adv_type(self._ranker, args)

    def run_adv_type(self, adv_type: Optional[AdvType], args: Args):
        if (adv_type is None):
            return None
        params = self._get_params(adv_type, args)
        mthd = adv_type.value(**params)
        return mthd

    def get_adv_name(self, adv_type: Union[Type[RefinerType],
                     Type[ClusterType], Type[RankerType]]) -> Optional[str]:
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

    def _get_name(self, typ: AdvType,
                  printed) -> str:
        # first get args
        args = self._get_args(typ)
        if (args is not None and len(args) > 0):
            if (printed):
                a = '_' + '_'.join(f'{k.replace("_", "-")}-{v}' for k, v
                                   in args.items())
            else:
                a = '(' + ','.join(f'{k}={v}' for k, v in args.items()) + ')'
        else:
            a = ''
        # then get name
        if (printed and hasattr(typ.value, '__print_name__')):
            name = typ.value.__print_name__.lower()
        elif (printed):
            name = typ.name.lower()
        else:
            name = typ.name.upper()
        return name + a

    def __repr__(self):
        return self._get_str()

    def get_file_name(self):
        return self._get_str(printed=True)
