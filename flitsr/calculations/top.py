from typing import Any
from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation
from flitsr.calculations.exp_values import cut_off_exp_val


def print_name(name: str):
    def fn(x: Any, ties: Ties, perc=False, collapse=False):
        return f"{name} top {x}"
    return fn


@calculation(print_name('one'), 'Display the expected value of finding at '
             'least one fault in the top `x` elements of the ranking (i.e. '
             'elements with the highest suspiciousness). The metric either '
             'returns 1 (if at least one fault is certainly found in the top '
             '`x` elements), or else the expected number of faults found.',
             'one-top', 'one-hit-at', 'one-accuracy-at')
def one_top_n(ties: Ties, x: int, collapse=False) -> float:
    k = cut_off_exp_val(ties, x, collapse=collapse)
    return min(1.0, k)


@calculation(print_name('all'), 'Display the expected value of the total '
             'number of faults found in the top `x` elements of the ranking '
             '(elements with the highest suspiciousness)', 'all-top',
             'all-hit-at', 'all-accuracy-at', 'top', 'hit-at', 'accuracy-at')
def all_top_n(ties: Ties, x: int, collapse=False) -> float:
    k = cut_off_exp_val(ties, x, collapse=collapse)
    return k


@calculation(print_name('perc'), 'Display the expected value of the '
             'percentage of faults found in the top `x` elements (elements '
             'with the highest suspiciousness)', 'perc-top')
def perc_top_n(ties: Ties, x: int, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 100
    else:
        k = cut_off_exp_val(ties, x, collapse=collapse)
        return (k/len(ties.faults))*100
