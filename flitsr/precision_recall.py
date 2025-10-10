from fractions import Fraction
from typing import Any, Dict, Tuple, Set
from math import comb, factorial
from flitsr.spectrum import Spectrum
from flitsr.tie import Ties


def precision(n: Any, ties: Ties, perc=False, worst_effort=False,
              collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    fault_num, total = method(n, ties, perc, worst_effort, collapse)
    return fault_num/total


def recall(n: Any, ties: Ties, perc=False, worst_effort=False,
           collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    fault_num, total = method(n, ties, perc, worst_effort, collapse)
    return fault_num/len(ties.faults)


def method(n: Any, ties: Ties, perc: bool, worst_effort: bool,
           collapse: bool) -> Tuple[float, int]:
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
