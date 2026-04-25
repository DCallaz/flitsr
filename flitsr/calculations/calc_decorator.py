import inspect
from typing import Union, Callable, Any, Collection, Optional
from flitsr import calculations


def calculation(print_name: Union[str, Callable[..., str]],
                desc: str, arg_name: str, *alt_arg_names: str) -> Callable:
    """
    A decorator for methods that perform calculations to specify that they
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
    def register_calc(fn):
        # first check if fn has required parameters
        argspec = inspect.getfullargspec(fn)
        not_in = []
        if ('ties' not in argspec.args):
            not_in.append('"ties"')
        if ('collapse' not in argspec.args):
            not_in.append('"collapse"')
        if (len(not_in) > 0):
            raise TypeError(f'Signature for function "{fn.__qualname__}" does '
                            'not match calculation signature; Does not contain'
                            f' parameter{"s" if len(not_in) > 1 else ""} '
                            f'{", or ".join(not_in)}')
        # register the calculation
        calculations.register_calc(fn, arg_name)
        arg_names = [arg_name] + [*alt_arg_names]
        setattr(fn, '__arg_names__', arg_names)
        # add the print name
        setattr(fn, '__print_name__', print_name)
        # add the description
        setattr(fn, '__doc__', desc)
        # ignore calculation parameters
        if (not hasattr(fn, '__existing__')):
            setattr(fn, '__existing__', list())
        existing = getattr(fn, '__existing__')
        existing.extend(['ties', 'collapse'])
        return fn
    return register_calc


def parameter(name: str, type: Optional[Callable[[str], Any]] = None,
              choices: Optional[Collection[Any]] = None):
    """
    A decorator for functions that perform calculations to specify additional
    information for a parameter of that calculation. Note: this decorator is
    only required for parameters where you need to convert the type, or specify
    choices. Other parameters will be automatically detected in the function
    signature, including default values.

    Args:
      name: The name of the paramter. Must be one of the parameters in the
        method signature.
      type: A function to convert the given parameter from a string into the
        type required. Will be used by the command-line parser.
    """
    def register_param(fn):
        if (type is not None):
            if (not hasattr(fn, '__types__')):
                setattr(fn, '__types__', dict())
            types_dict = getattr(fn, '__types__')
            types_dict[name] = type
        if (choices is not None):
            if (not hasattr(fn, '__choices__')):
                setattr(fn, '__choices__', dict())
            choices_dict = getattr(fn, '__choices__')
            choices_dict[name] = choices
        return fn
    return register_param
