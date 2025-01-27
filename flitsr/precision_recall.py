import copy
from typing import Any, Dict, List, Tuple
from math import comb, factorial
from flitsr.spectrum import Spectrum
from flitsr.tie import Ties


def precision(n: Any, ties: Ties, spectrum: Spectrum, perc=False,
              worst_effort=False, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    fault_num, total = method(n, ties, spectrum, perc, worst_effort, collapse)
    return fault_num/total


def recall(n: Any, ties: Ties, spectrum: Spectrum, perc=False,
           worst_effort=False, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    fault_num, total = method(n, ties, spectrum, perc, worst_effort, collapse)
    return fault_num/len(ties.faults)


def method(n: Any, ties: Ties, spectrum: Spectrum, perc: bool,
           worst_effort: bool, collapse: bool) -> Tuple[float, int]:
    size = 0
    if (collapse):
        size = len(spectrum.groups())
    else:
        for group in spectrum.groups():
            size += len(group.get_elements())
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
            add = 0.0
            if (total+tie.len(collapse) > n and tie.num_faults() > 0):
                p = int(n - total)
                m = tie.len(collapse)
                n_l = tie.num_fault_locs(collapse)
                fpl = tie.num_faults()/n_l
                outer_top = factorial(m-p) * factorial(p)
                outer_bot = factorial(m)
                for x in range(1, p+1):
                    add += fpl*x*((comb(n_l, x) * comb(m - n_l, p - x) *
                                   outer_top)/outer_bot)
                # for i in range(curr_faults):
                #     expected_value = (i+1)*(len(uuts)+1)/(curr_faults+1)
                #     if (expected_value <= x):
                #         add += 1
                total += p
            else:
                add = tie.num_faults()
                total += tie.len(collapse)
            fault_num += add
    except StopIteration:
        pass
    return fault_num, total
