import argparse
from functools import partial
from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation, parameter, timing
from flitsr.calculations.exp_values import effort_exp_val


@calculation("wasted effort (first)",
             "Display the wasted effort to the first fault", "first")
def first(ties: Ties, collapse: bool) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    return effort_exp_val(ties, 1, weffort=True, collapse=collapse)


@calculation("wasted effort (average)",
             "Display the wasted effort to the average fault",
             "average", "avg")
def average(ties: Ties, collapse: bool) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    return effort_exp_val(ties, len(ties.faults), weffort=True, avg=True,
                          collapse=collapse)


@calculation("wasted effort (median)",
             "Display the wasted effort to the median fault",
             "median", "med")
def median(ties: Ties, collapse: bool) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    if (len(ties.faults) % 2 == 1):
        return effort_exp_val(ties, int((len(ties.faults)+1)/2), weffort=True,
                              collapse=collapse)
    else:
        m1 = effort_exp_val(ties, int(len(ties.faults)/2), weffort=True,
                            collapse=collapse)
        m2 = effort_exp_val(ties, int(len(ties.faults)/2)+1, weffort=True,
                            collapse=collapse)
        return (m1+m2)/2


@calculation("wasted effort (last)",
             "Display the wasted effort to the last fault",
             "last")
def last(ties: Ties, collapse: bool) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    return effort_exp_val(ties, len(ties.faults), weffort=True,
                          collapse=collapse)


def check_fault_type(nth: str):
    """check type of general weffort"""
    if (nth.isdigit() and int(nth) > 0):
        return int(nth)
    else:
        raise argparse.ArgumentTypeError(f'Invalid fault number {nth}')


def nth_print_name(name: str, ties: Ties, collapse: bool, n: int):
    return f"{name} ({n})"


@calculation(partial(nth_print_name, name='wasted effort'),
             "Display the wasted effort to the Nth fault",
             "weffort", "wasted-effort")
@parameter('n', type=check_fault_type)
def nth(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    return effort_exp_val(ties, n, weffort=True,
                          collapse=collapse)
