import importlib
import pkgutil
import sys
from enum import Enum
from flitsr import input

_inputs = {}


def register_input(cls):
    _inputs[cls.__name__.upper()] = cls


# load local inputs
__all__ = [m[1] for m in pkgutil.iter_modules(input.__path__)]
for module in __all__:
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
