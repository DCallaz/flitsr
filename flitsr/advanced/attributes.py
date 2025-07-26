from typing import Collection, Any


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


def choices(param: str, choices: Collection[Any]):
    """
    An advanced types decorator to specfiy the choices available for a given
    parameter. The given choices will be added as available choices for the
    command line argument for FLITSR.

    Args:
      param: str: The parameter to set choices for.
      choices: Collection[Any]: The collection of choices for the parameter.
    """
    def add_choices(fn):
        if (not hasattr(fn, '__choices__')):
            setattr(fn, '__choices__', dict())
        choices_dict = getattr(fn, '__choices__')
        choices_dict[param] = choices
        return fn
    return add_choices


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
