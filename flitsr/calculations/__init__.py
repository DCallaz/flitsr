import pkgutil
import sys
import importlib
from typing import Union, Callable
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from flitsr import calculations

calcs = {}


def register_calc(cls, name: str):
    calcs[name] = cls


# load local calculations
__all__ = [m[1] for m in pkgutil.iter_modules(calculations.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)
# load plugin calculations
adv_entry_points = entry_points(group='flitsr.calculation')
for adv_ep in adv_entry_points:
    adv_ep.load()


def calculation(print_name: Union[str, Callable[..., str]],
                desc: str, arg_name: str, *alt_arg_names: str) -> Callable:
    """A decorator for methods that perform calculations to specify that they
    should be made available as calculations.

    Args:
      print_name: str: The name of the calculation when printing out. Can be a
          string, or function that takes the calculations parameters and returns
          a string.
      desc: str: A breif description of the calculation to show in the help
          messages
      arg_name: str: The main command line argument name.
      alt_arg_names: str: Alternate command line argument names.
    """
    def register_calc(cls):
        # register the calculation
        calculations.register_calc(cls, arg_name)
        arg_names = [arg_name] + [*alt_arg_names]
        setattr(cls, '__arg_names__', arg_names)
        # add the print name
        setattr(cls, '__print_name__', print_name)
        return cls
    return register_calc
