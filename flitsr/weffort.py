import copy
from typing import Dict, List, Set, Iterator, Tuple, Optional
from flitsr.score import Ties
from flitsr.spectrum import Spectrum


def first(ties: Ties, c: bool):
    if (len(ties.faults) == 0):
        return 0
    return method(ties, 1, collapse=c)


def average(ties: Ties, c: bool):
    if (len(ties.faults) == 0):
        return 0
    return method(ties, len(ties.faults), avg=True, collapse=c)


def median(ties: Ties, c: bool):
    if (len(ties.faults) == 0):
        return 0
    if (len(ties.faults) % 2 == 1):
        return method(ties, int((len(ties.faults)+1)/2), False, c)
    else:
        m1 = method(ties, int(len(ties.faults)/2), False, c)
        m2 = method(ties, int(len(ties.faults)/2)+1, False, c)
        return (m1+m2)/2


def last(ties: Ties, c: bool):
    if (len(ties.faults) == 0):
        return 0
    return method(ties, len(ties.faults), collapse=c)


def nth(ties: Ties, n: int, c: bool):
    if (len(ties.faults) == 0):
        return 0
    return method(ties, min(len(ties.faults), n), collapse=c)

# <---------------- Helper functions --------------->


def method(ties: Ties, target, avg=False, collapse=False,
           worst_effort=False) -> float:
    found = False
    actual = 0
    effort = 0
    efforts = []
    tie_iter = iter(ties)
    while (not found):
        tie = next(tie_iter)
        # print(tie)
        actual += tie.num_faults
        found = (actual >= target)
        if (avg):
            for j in range(1, tie.num_faults+1):
                if (collapse):
                    efforts.append(effort +
                                   j*((tie.group_len+1)/(tie.fault_groups+1)-1))
                else:
                    efforts.append(effort +
                                   j*((len(tie.elems)+1)/(tie.fault_locs+1)-1))
        if (not found):
            if (collapse):
                effort += tie.group_len - tie.fault_groups
            else:
                effort += len(tie.elems) - tie.fault_locs
        else:
            if (collapse):
                k = target + tie.num_faults - actual
                effort += k*((tie.group_len+1)/(tie.fault_groups+1)-1)
            else:
                k = target + tie.num_faults - actual
                effort += k*((len(tie.elems)+1)/(tie.fault_locs+1)-1)
    if (avg):
        return sum(efforts)/target
    else:
        return effort
