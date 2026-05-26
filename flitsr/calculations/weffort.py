import argparse
from functools import partial
from flitsr.tie import Ties, Tie
from flitsr.calculations.bu_model import BUModel
from flitsr.calculations.calc_decorator import calculation, parameter, \
        timing, get_runtime
from flitsr.calculations.exp_values import effort_exp_val
from flitsr.calculations.perms import exact_method, Calc


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
@parameter('n', type=check_fault_type)
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
@parameter('n', type=check_fault_type)
def steimann_rt(ties: Ties, collapse: bool, n: int) -> float:
    return get_runtime('steimann', {'n': n})


@calculation(partial(nth_print_name, name='wasted effort runtime'),
             "Display the runtime for calculating the wasted effort to the "
             "Nth fault", "weffort-time")
@parameter('n', type=check_fault_type)
def weffort_rt(ties: Ties, collapse: bool, n: int) -> float:
    return get_runtime('nth', {'n': n})


@calculation(partial(nth_print_name, name='full sampled effort'),
             "Display the (full sampled) wasted effort to the Nth fault",
             "f-sampled", "full-sampled-wasted-effort")
@parameter('n', type=check_fault_type)
@timing
def full_sampled(ties: Ties, collapse: bool, n: int) -> float:
    return effort_exp_val(ties, min(len(ties.faults), n), weffort=True,
                          collapse=collapse,
                          tie_exp_func=partial(_sampled, bu=ties.bu_model))


def nth_sampled_print_name(name: str, ties: Ties, collapse: bool, n: int,
                           samples: int):
    return f"{samples} {name} ({n})"


@calculation(partial(nth_sampled_print_name, name='partial sampled effort'),
             "Display the (partial sampled) wasted effort to the Nth fault",
             "p-sampled", "partial-sampled-wasted-effort")
@parameter('n', type=check_fault_type)
@timing
def partial_sampled(ties: Ties, collapse: bool, n: int, samples: int) -> float:
    return effort_exp_val(ties, min(len(ties.faults), n), weffort=True,
                          collapse=collapse,
                          tie_exp_func=partial(_sampled, bu=ties.bu_model,
                                               samples=samples))


def _sampled(tie: Tie, k: int, weffort: bool, collapse=False,
             bu: BUModel = BUModel.PERFECT, samples=None) -> float:
    return exact_method(tie.active_fault_locations(collapse), k,
                        tie.elems(collapse, no_passive=True), Calc.WEFFORT,
                        bu=bu, samples=samples)


@calculation(partial(nth_print_name, name='full sampled runtime'),
             "Display the runtime for (full sampled) wasted effort to the Nth "
             "fault", "full-sampled-time")
@parameter('n', type=check_fault_type)
def full_sampled_rt(ties: Ties, collapse: bool, n: int) -> float:
    return get_runtime('full_sampled', {'n': n})


@calculation(partial(nth_sampled_print_name, name='partial sampled runtime'),
             "Display the runtime for (partial sampled) wasted effort to the "
             "Nth fault", "partial-sampled-time")
@parameter('n', type=check_fault_type)
def partial_sampled_rt(ties: Ties, collapse: bool, n: int,
                       samples: int) -> float:
    return get_runtime('partial_sampled', {'n': n, 'samples': samples})
