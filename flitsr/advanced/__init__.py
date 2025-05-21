import pkgutil
from flitsr import advanced
from enum import Enum

rankers = {}
clusters = {}
refiners = {}
all_types = {}


def register_ranker(cls):
    rankers[cls.__name__] = cls
    all_types[cls.__name__] = cls


def register_cluster(cls):
    clusters[cls.__name__] = cls
    all_types[cls.__name__] = cls


def register_refiner(cls):
    refiners[cls.__name__] = cls
    all_types[cls.__name__] = cls


__all__ = [m[1] for m in pkgutil.iter_modules(advanced.__path__)]
from . import *

RefinerType = Enum('RefinerType', " ".join(refiners.keys()))  # type:ignore
ClusterType = Enum('ClusterType', " ".join(clusters.keys()))  # type:ignore
RankerType = Enum('RankerType', " ".join(rankers.keys()))  # type:ignore
