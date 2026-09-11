import importlib
import pkgutil
import sys
from typing import Type, Any
from enum import Enum
from flitsr import ranking_input

_ranking_inputs = {}


def register_ranking_input(cls: Type[Any]) -> None:
    _ranking_inputs[cls.__name__.upper()] = cls

#  Exposed imports
from flitsr.ranking_input.ranking_reader import RankingInput  # noqa
from flitsr.ranking_input.flitsr_ranking import FlitsrRanking  # noqa
from flitsr.ranking_input.gzoltar_ranking import GzoltarRanking  # noqa
__all__ = ['RankingInput', 'RankingInputType', 'FlitsrRanking',
           'GzoltarRanking']

# load local inputs
__all = [m[1] for m in pkgutil.iter_modules(ranking_input.__path__)]
for module in __all:
    importlib.import_module('.'+module, package=__name__)
# load plugin inputs
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points
adv_entry_points = entry_points(group='flitsr.ranking_input')
for adv_ep in adv_entry_points:
    adv_ep.load()

RankingInputType = Enum('RankingInputType', _ranking_inputs,  # type:ignore
                        module=ranking_input,
                        qualname='ranking_input.RankingInputType')
