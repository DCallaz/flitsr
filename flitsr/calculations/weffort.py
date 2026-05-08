import argparse
from functools import partial
from datetime import timedelta
import time
from functools import wraps
from collections import defaultdict
from typing import Dict
from flitsr.tie import Ties, Tie
from flitsr.calculations.bu_model import BUModel
from flitsr.calculations.calc_decorator import calculation, parameter
from flitsr.calculations.exp_values import effort_exp_val
from flitsr.calculations.perms import exact_method, Calc


runtimes: Dict[str, Dict[int, float]] = defaultdict(defaultdict)


def timing(f):
    @wraps(f)
    def wrap(ties: Ties, collapse: bool, n: int):
        start = time.time()
        result = f(ties, collapse, n)
        end = time.time()
        runtimes[f.__name__][n] = (end - start)
        return result
    return wrap


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
@timing
def nth(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    return effort_exp_val(ties, min(len(ties.faults), n), weffort=True,
                          collapse=collapse)


@calculation(partial(nth_print_name, name='steimann effort'),
             "Display the (steimann) wasted effort to the Nth fault",
             "steimann", "steimann-wasted-effort")
@timing
def steimann(ties: Ties, collapse: bool, n: int) -> float:
    return effort_exp_val(ties, min(len(ties.faults), n), weffort=True,
                          collapse=collapse, tie_exp_func=_steimann)


def _steimann(tie: Tie, k: int, weffort: bool, collapse=False) -> float:
    n = tie.len(collapse)
    m = tie.num_faults()
    return (k * (n-m))/(m+1)


@calculation(partial(nth_print_name, name='steimann runtime'),
             "Display the runtime for (steimann) wasted effort to the Nth fault",
             "steimann-time")
def steimann_rt(ties: Ties, collapse: bool, n: int) -> float:
    return runtimes['steimann'][n]


@calculation(partial(nth_print_name, name='wasted effort runtime'),
             "Display the runtime for calculating the wasted effort to the "
             "Nth fault", "weffort-time")
def weffort_rt(ties: Ties, collapse: bool, n: int) -> float:
    return runtimes['nth'][n]


@calculation(partial(nth_print_name, name='sampled effort'),
             "Display the (sampled) wasted effort to the Nth fault",
             "sampled", "sampled-wasted-effort")
@timing
def sampled(ties: Ties, collapse: bool, n: int) -> float:
    return effort_exp_val(ties, min(len(ties.faults), n), weffort=True,
                          collapse=collapse,
                          tie_exp_func=partial(_sampled, bu=ties.bu_model))


def _sampled(tie: Tie, k: int, weffort: bool, collapse=False,
             bu: BUModel = BUModel.PERFECT) -> float:
    return exact_method(tie.active_fault_locations(), k, tie.elems(),
                        Calc.WEFFORT, bu=bu)


@calculation(partial(nth_print_name, name='sampled runtime'),
             "Display the runtime for (sampled) wasted effort to the Nth fault",
             "sampled-time")
def sampled_rt(ties: Ties, collapse: bool, n: int) -> float:
    return runtimes['sampled'][n]
