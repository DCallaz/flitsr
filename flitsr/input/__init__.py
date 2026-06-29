import importlib
import pkgutil
import sys
from enum import Enum, auto
from flitsr import input

_inputs = {}


class BaseInputType(Enum):
    DIR = auto()
    FILE = auto()


def register_input(cls):
    _inputs[cls.__name__.upper()] = cls

#  Exposed imports
from flitsr.input.input_reader import Input, FileInput, DirInput  # noqa
from flitsr.input.tcm_input import TCM  # noqa
from flitsr.input.gzoltar_input import Gzoltar  # noqa
__all__ = ['Input', 'TCM', 'Gzoltar', 'InputType']

# load local inputs
__all = [m[1] for m in pkgutil.iter_modules(input.__path__)]
for module in __all:
    importlib.import_module('.'+module, package=__name__)
# load plugin inputs
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points
adv_entry_points = entry_points(group='flitsr.input')
for adv_ep in adv_entry_points:
    adv_ep.load()

InputType = Enum('InputType', _inputs,  # type:ignore
                 module=input, qualname='input.InputType')
