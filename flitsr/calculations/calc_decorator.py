import inspect
import time
from typing import Union, Callable, Any, Collection, Optional, Dict
from collections import defaultdict
from functools import wraps
from flitsr import calculations


def calculation(print_name: Union[str, Callable[..., str]],
                desc: str, arg_name: str, *alt_arg_names: str) -> Callable:
    """
    A decorator for methods that perform calculations to specify that they
    should be made available as calculations. NOTE: this decorator must be
    executed after (i.e., must be placed above) any other custom decorators
    which are intended to be processed when the function is run (this does not
    include the `parameter` decorator, which may be placed in any order).

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
        fn_unw = inspect.unwrap(fn)
        argspec = inspect.getfullargspec(fn_unw)
        not_in = []
        if ('ties' not in argspec.args):
            not_in.append('"ties"')
        if ('collapse' not in argspec.args):
            not_in.append('"collapse"')
        if (len(not_in) > 0):
            raise TypeError(f'Signature for function "{fn_unw.__qualname__}" '
                            'does not match calculation signature; Does not '
                            f'contain parameter{"s" if len(not_in) > 1 else ""} '
                            f'{", or ".join(not_in)}')
        # register the calculation
        calculations.register_calc(fn, arg_name)
        arg_names = [arg_name] + [*alt_arg_names]
        setattr(fn_unw, '__arg_names__', arg_names)
        # add the print name
        setattr(fn_unw, '__print_name__', print_name)
        # add the description
        setattr(fn_unw, '__doc__', desc)
        # ignore calculation parameters
        if (not hasattr(fn_unw, '__existing__')):
            setattr(fn_unw, '__existing__', list())
        existing = getattr(fn_unw, '__existing__')
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
      choices: A `Collection` of values which the given parameter can take on.
    """
    def register_param(fn):
        fn_unw = inspect.unwrap(fn)
        if (type is not None):
            if (not hasattr(fn_unw, '__types__')):
                setattr(fn_unw, '__types__', dict())
            types_dict = getattr(fn_unw, '__types__')
            types_dict[name] = type
        if (choices is not None):
            if (not hasattr(fn_unw, '__choices__')):
                setattr(fn_unw, '__choices__', dict())
            choices_dict = getattr(fn_unw, '__choices__')
            choices_dict[name] = choices
        return fn
    return register_param


runtimes: Dict[str, Any] = defaultdict(defaultdict)


def timing(func: Callable):
    @wraps(func)
    def wrap(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        sig = inspect.signature(inspect.unwrap(func))
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        args = bound.arguments
        # remove the default ties and collapse (don't worry here if not found)
        args.pop('ties', None)
        args.pop('collapse', None)
        if (len(args) > 0):
            runtimes[func.__name__][arg_tup(args)] = (end - start)
        else:
            runtimes[func.__name__] = (end - start)
        return result
    return wrap


def get_runtime(func_name, args: Dict[str, Any]) -> float:
    return runtimes[func_name][arg_tup(args)]


def arg_tup(args):
    return tuple(sorted(args.items()))
