import copy
from typing import Any, Dict, List, Tuple
from math import comb, factorial
from flitsr.weffort import getTie
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


def precision(n: Any, faults: Dict[int, List[Spectrum.Element]],
              scores: Scores, spectrum: Spectrum, perc=False,
              worst_effort=False, collapse=False) -> float:
    if (len(faults) == 0):
        return 0.0
    fault_num, total = method(n, faults, scores, spectrum, perc,
                              worst_effort, collapse)
    return fault_num/total


def recall(n: Any, faults: Dict[int, List[Spectrum.Element]],
           scores: Scores, spectrum: Spectrum, perc=False,
           worst_effort=False, collapse=False) -> float:
    if (len(faults) == 0):
        return 0.0
    fault_num, total = method(n, faults, scores, spectrum, perc,
                              worst_effort, collapse)
    return fault_num/len(faults)


def method(n: Any, faults: Dict[int, List[Spectrum.Element]], scores: Scores,
           spectrum: Spectrum, perc: bool, worst_effort: bool,
           collapse: bool) -> Tuple[int, int]:
    size = 0
    if (collapse):
        size = len(spectrum.groups)
    else:
        for group in spectrum.groups:
            size += len(group)
    if (n == "b"):
        n = -1
    elif (n == "f"):
        n = len(faults)
    elif (perc):
        n = n * size
    faults = copy.deepcopy(faults) # needed to remove groups of fault locations
    s_iter = iter(scores)
    total = 0
    cached = None
    fault_num = 0
    try:
        while (total < n):
            uuts, group_len, curr_faults, curr_faulty_groups, \
                cached = getTie(faults, s_iter, spectrum, cached, worst_effort)
            if (collapse):  # TODO: actual calculation for collapse
                add = 0
                if (total+group_len > n and curr_faulty_groups > 0):
                    x = n - total
                    for i in range(curr_faulty_groups):
                        expected_value = (i+1)*(group_len+1)/(curr_faulty_groups+1)
                        if (expected_value <= x):
                            add += 1
                    total += x
                else:
                    add = curr_faulty_groups
                    total += group_len
                fault_num += add
            else:
                add = 0
                if (total+len(uuts) > n and curr_faults[0] > 0):
                    p = int(n - total)
                    m = len(uuts)
                    n_f = curr_faults[1]
                    outer_top = factorial(m-p) * factorial(p)
                    outer_bot = factorial(m)
                    for x in range(1, p+1):
                        add += x*(comb(n_f, x) * comb(m - n_f, p - x) *
                                  outer_top)/outer_bot
                    # for i in range(curr_faults):
                    #     expected_value = (i+1)*(len(uuts)+1)/(curr_faults+1)
                    #     if (expected_value <= x):
                    #         add += 1
                    total += p
                else:
                    add = curr_faults[0]
                    total += len(uuts)
                fault_num += add
    except StopIteration:
        pass
    return fault_num, total
