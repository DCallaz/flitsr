import importlib
import pkgutil
from enum import Enum
from flitsr import input

_inputs = {}


def register_input(cls):
    _inputs[cls.__name__.upper()] = cls


__all__ = [m[1] for m in pkgutil.iter_modules(input.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)

InputType = Enum('InputType', _inputs,  # type:ignore
                 module=input, qualname='input.InputType')
