from __future__ import annotations
import pkgutil
from flitsr import advanced
from enum import Enum
import importlib
from typing import Union

_rankers = {}
_clusters = {}
_refiners = {}
all_types = {}


def register_ranker(cls):
    _rankers[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_cluster(cls):
    _clusters[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


def register_refiner(cls):
    _refiners[cls.__name__.upper()] = cls
    all_types[cls.__name__.upper()] = cls


__all__ = [m[1] for m in pkgutil.iter_modules(advanced.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)

RefinerType = Enum('RefinerType', _refiners,  # type:ignore
                   module=advanced, qualname='advanced.RefinerType')
ClusterType = Enum('ClusterType', _clusters,  # type:ignore
                   module=advanced, qualname='advanced.ClusterType')
RankerType = Enum('RankerType', _rankers,  # type:ignore
                  module=advanced, qualname='advanced.RankerType')


class Config:
    def __init__(self, ranker: RankerType = None,
                 cluster: ClusterType = None):
        self.cluster = cluster
        self.ranker = ranker

    def __str__(self):
        return self._get_str()

    def _get_str(self, printed=False):
        if (printed):
            c = '_'
        else:
            c = '+'
        if (self.cluster is None):
            if (self.ranker is None):
                return self._get_name(RankerType['SBFL'], printed)
            else:
                return self._get_name(self.ranker, printed)
        else:
            if (self.ranker is None):
                return self._get_name(self.cluster, printed)
            else:
                return (self._get_name(self.cluster, printed) + c +
                        self._get_name(self.ranker, printed))

    def _get_name(self, typ: Union[RefinerType, ClusterType, RankerType],
                  printed) -> str:
        if (printed and hasattr(typ.value, '_print_name')):
            return typ.value._print_name.lower()
        elif (printed):
            return typ.name.lower()
        else:
            return typ.name.upper()

    def __repr__(self):
        return self._get_str()

    def get_file_name(self):
        return self._get_str(printed=True)
