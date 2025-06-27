from __future__ import annotations
import pkgutil
from flitsr import advanced
from enum import Enum
import importlib
from typing import Union
import sys

_rankers = {}
_clusters = {}
_refiners = {}
all_types = {}
all_types_print = []


def register_ranker(cls):
    _rankers[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_cluster(cls):
    _clusters[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_refiner(cls):
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

for cls in all_types.values():
    if (hasattr(cls, '__print_name__')):
        all_types_print.append(cls.__print_name__.lower())
    else:
        all_types_print.append(cls.__name__.lower())


class Config:
    def __init__(self, ranker: RankerType = None, cluster: ClusterType = None,
                 refiner: RefinerType = None):
        self.cluster = cluster
        self.ranker = ranker
        self.refiner = refiner

    def __str__(self):
        return self._get_str()

    def _get_str(self, printed=False):
        c = '_' if printed else '+'
        components = [self.ranker or RankerType['SBFL'], self.refiner,
                      self.cluster]
        string = c.join(self._get_name(c, printed) for c in components
                        if c is not None)
        return string

    def _get_name(self, typ: Union[RefinerType, ClusterType, RankerType],
                  printed) -> str:
        if (printed and hasattr(typ.value, '__print_name__')):
            return typ.value.__print_name__.lower()
        elif (printed):
            return typ.name.lower()
        else:
            return typ.name.upper()

    def __repr__(self):
        return self._get_str()

    def get_file_name(self):
        return self._get_str(printed=True)
