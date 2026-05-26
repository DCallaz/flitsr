import pkgutil
import sys
import importlib
import inspect
from typing import Dict
from collections.abc import Callable
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from flitsr.calculations.bu_model import BUModel  # noqa
from flitsr import calculations

calcs: Dict[str, Callable] = {}
calcs_base: Dict[str, Callable] = {}


def register_calc(func, name: str):
    calcs[name] = func
    calcs_base[name] = inspect.unwrap(func)


# load local calculations
__all__ = [m[1] for m in pkgutil.iter_modules(calculations.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)
# load plugin calculations
adv_entry_points = entry_points(group='flitsr.calculation')
for adv_ep in adv_entry_points:
    adv_ep.load()
