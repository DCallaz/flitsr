from typing import Collection, Any, Optional, Callable
from functools import partial
import inspect
from deprecated.sphinx import versionadded


def existing(*params: str):
    """
    A python decorator to mark the given parameter(s) as one(s) already defined
    in FLITSR's arguments. These parameters for the decorated advanced type are
    therefore not added as FLITSR command line arguments, but are instead taken
    from the existing command line arguments.

    Args:
      *params: str: The parameters of the __init__ function to mark as already
        existing ``flitsr`` parameters.
    """
    def add_existing(fn):
        if (not hasattr(fn, '__existing__')):
            setattr(fn, '__existing__', list())
        existing = getattr(fn, '__existing__')
        for param in params:
            existing.append(param)
        return fn
    return add_existing


def _add_choices(fn, param, choices):
    if (not hasattr(fn, '__choices__')):
        setattr(fn, '__choices__', dict())
    choices_dict = getattr(fn, '__choices__')
    choices_dict[param] = choices
    return fn


def choices(param: str, choices: Collection[Any]):
    """
    An advanced types decorator to specfiy the choices available for a given
    parameter. The given choices will be added as available choices for the
    command line argument for FLITSR. NOTE: this decorator is equivalent to
    `parameter(param, choices=choices)<flitsr.advanced_types.attributes.parameter>`.

    Args:
      param: str: The parameter to set choices for.
      choices: Collection[Any]: The collection of choices for the parameter.
    """
    return partial(_add_choices, param=param, choices=choices)


@versionadded(version='2.5.0')
def parameter(name: str, type: Optional[Callable[[str], Any]] = None,
              choices: Optional[Collection[Any]] = None,
              existing: bool = False):
    """
    A decorator for advanced types to specify additional information for a
    parameter for that advanced type. Note: this decorator is only required for
    parameters where you need to convert the type, or specify choices. Other
    parameters will be automatically detected in the function signature,
    including default values.

    Args:
      name: The name of the paramter. Must be one of the parameters in the
        method signature.
      type: A function to convert the given parameter from a string into the
        type required. Will be used by the command-line parser.
      choices: The collection of choices for the parameter (see `choices` for
        more details).
      existing: Whether to mark the given parameter as one already defined
        in FLITSR's arguments (see `existing` for more details).
    """
    def register_param(fn):
        fn_unw = inspect.unwrap(fn)
        if (type is not None):
            if (not hasattr(fn_unw, '__types__')):
                setattr(fn_unw, '__types__', dict())
            types_dict = getattr(fn_unw, '__types__')
            types_dict[name] = type
        if (choices is not None):
            _add_choices(fn_unw, name, choices)
        if (existing):
            if (not hasattr(fn_unw, '__existing__')):
                setattr(fn_unw, '__existing__', list())
            getattr(fn_unw, '__existing__').append(name)
        return fn
    return register_param


def print_name(print_name: str):
    """
    An advanced types decorator to specfiy an alternative name for the
    decorated class to use when printing results to a file. By default the
    lower-case name of the advanced type is used.

    Args:
      print_name: str: The name to use when printing this advanced type.
    """
    def add_print_name(cls):
        setattr(cls, '__print_name__', print_name)
        return cls
    return add_print_name
