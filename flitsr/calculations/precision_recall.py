from fractions import Fraction
from typing import Any, Tuple
from math import comb
from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation, parameter


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
    fault_num, total = method(x, ties, False, collapse)
    return fault_num/total


@calculation(print_name('recall'), 'Displays recall values at a given rank '
             '`x`. Recall is the amount of faults f found within the cut-off '
             'point `x`, out of the total number of faults n (i.e. f/n). Can '
             'be specified multiple times', 'recall-at')
@parameter('x', type=stop_type)
def recall(x: Any, ties: Ties, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    fault_num, total = method(x, ties, False, collapse)
    return fault_num/len(ties.faults)


def method(n: Any, ties: Ties, perc: bool = False,
           collapse: bool = False) -> Tuple[float, int]:
    size = ties.size(collapse)
    if (n == "b"):
        n = -1
    elif (n == "f"):
        n = len(ties.faults)
    elif (perc):
        n = n * size
    tie_iter = iter(ties)
    total = 0
    fault_num = 0.0
    try:
        while (total < n):
            tie = next(tie_iter)
            faults = tie.active_faults(collapse)
            add = 0.0
            if (total+tie.len(collapse) > n and tie.num_faults() > 0):
                p = int(n - total)  # num of statements to inspect in the tie
                Ntot = tie.len(collapse)  # total num of statements in the tie
                expval = 0.0
                # sum the expected values of finding each fault
                for f in faults:
                    Ni = len(faults[f])
                    # Expected value of each fault is {1, 0} <=> probability
                    # P(selecting one or more locations of this fault)
                    # <=> 1 - P(selecting no locations of this fault)
                    expval += 1 - Fraction(comb(Ntot-Ni, p), comb(Ntot, p))
                add += float(expval)  # add the expected # of faults found in p
                total += p
            else:
                add = tie.num_faults()
                total += tie.len(collapse)
            fault_num += add
    except StopIteration:
        pass
    return fault_num, total
