from typing import Any
from flitsr.tie import Ties
from flitsr.calculations.precision_recall import method
from flitsr.calculations.calc_decorator import calculation


def print_name(name: str):
    def fn(x: Any, ties: Ties, perc=False, collapse=False):
        return f"{name} top {x}"
    return fn


@calculation(print_name('one'), 'Display the expected value of finding at '
             'least one fault in the top `x` elements (elements with the '
             'highest suspiciousness).', 'one-top')
def one_top_n(ties: Ties, x: int, collapse=False) -> float:
    k, _ = method(x, ties, collapse=collapse)
    return min(1.0, k)


@calculation(print_name('all'), 'Display the expected value of the total '
             'number of faults found in the top `x` elements (elements with '
             'the highest suspiciousness)', 'all-top')
def all_top_n(ties: Ties, x: int, collapse=False) -> float:
    k, _ = method(x, ties, collapse=collapse)
    return k


@calculation(print_name('perc'), 'Display the expected value of the '
             'percentage of faults found in the top `x` elements (elements '
             'with the highest suspiciousness)', 'perc-top')
def perc_top_n(ties: Ties, x: int, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 100
    else:
        k, _ = method(x, ties, collapse=collapse)
        return (k/len(ties.faults))*100
