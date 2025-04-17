import pkgutil
from flitsr import advanced
from enum import Enum

rankers = {}
clusters = {}
all_types = {}


def register_ranker(cls):
    rankers[cls.__name__] = cls
    all_types[cls.__name__] = cls


def register_cluster(cls):
    clusters[cls.__name__] = cls
    all_types[cls.__name__] = cls


__all__ = [m[1] for m in pkgutil.iter_modules(advanced.__path__)]
from . import *

ClusterType = Enum('ClusterType', " ".join(clusters.keys()))
RankerType = Enum('RankerType', " ".join(rankers.keys()))
