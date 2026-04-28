from fractions import Fraction
from typing import Any, Tuple
from math import comb
from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation, parameter
from flitsr.calculations.exp_values import cut_off_exp_val


# Precision recall type functions
def stop_type(value: str):
    if (value == "b" or value == "f"):
        return value
    elif (value.isdigit()):
        return int(value)
    else:
        raise ValueError(str(value)+" is not a valid precision/recall "
                         "string value")


def print_name(name: str):
    def fn(x: Any, ties: Ties, perc=False, collapse=False):
        return f"{name} at {x}"
    return fn


@calculation(print_name('precision'), 'Displays precision values at a given '
             'rank `x`. Precision is the amount of faults f found within the '
             'cut-off point `x`, out of the number of elements seen '
             '(i.e. f/x). Can be specified multiple times', 'precision-at')
@parameter('x', type=stop_type)
def precision(x: Any, ties: Ties, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    n = _get_n(x, ties, collapse=collapse)
    fault_num = cut_off_exp_val(ties, n, collapse=collapse)
    return fault_num/n


@calculation(print_name('recall'), 'Displays recall values at a given rank '
             '`x`. Recall is the amount of faults f found within the cut-off '
             'point `x`, out of the total number of faults n (i.e. f/n). Can '
             'be specified multiple times', 'recall-at')
@parameter('x', type=stop_type)
def recall(x: Any, ties: Ties, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    n = _get_n(x, ties, collapse=collapse)
    fault_num = cut_off_exp_val(ties, n, collapse=collapse)
    return fault_num/len(ties.faults)


def _get_n(x: Any, ties: Ties, perc=False, collapse=False) -> int:
    size = ties.size(collapse)
    if (x == "b"):
        n = -1
    elif (x == "f"):
        n = len(ties.faults)
    elif (perc):
        n = x * size
    return n
