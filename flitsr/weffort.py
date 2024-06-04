import copy
from typing import Dict, List, Iterator, Optional
from flitsr.output import find_group
from flitsr.score import Scores
from flitsr.spectrum import Spectrum


def first(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
          spectrum: Spectrum, c: bool):
    if (len(faults) == 0):
        return 0
    return method(faults, scores, spectrum, 1, collapse=c)


def average(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
            spectrum: Spectrum, c: bool):
    if (len(faults) == 0):
        return 0
    return method(faults, scores, spectrum, len(faults), True, c)


def median(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
           spectrum: Spectrum, c: bool):
    if (len(faults) == 0):
        return 0
    if (len(faults) % 2 == 1):
        return method(faults, scores, spectrum,
                      int((len(faults)+1)/2), False, c)
    else:
        m1 = method(faults, scores, spectrum, int(len(faults)/2), False, c)
        m2 = method(faults, scores, spectrum, int(len(faults)/2)+1, False, c)
        return (m1+m2)/2


def last(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
         spectrum: Spectrum, c: bool):
    if (len(faults) == 0):
        return 0
    return method(faults, scores, spectrum, len(faults), collapse=c)

# <---------------- Helper functions --------------->


def method(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
           spectrum: Spectrum, target, avg=False,
           collapse=False, worst_effort=False):
    faults = copy.deepcopy(faults)  # need for remove groups of fault locations
    found = False
    actual = 0
    effort = 0
    efforts = []
    cached = None
    s_iter = iter(scores)
    while (not found):
        uuts, group_len, curr_faults, curr_faulty_groups, \
                cached = getTie(faults, s_iter, spectrum, cached, worst_effort)
        # print(uuts, group_len, curr_faults, curr_faulty_groups, cached)
        actual += curr_faults[0]
        found = (actual >= target)
        if (avg):
            for j in range(1, curr_faults[0]+1):
                if (collapse):
                    efforts.append(effort +
                                   j*((group_len+1)/(curr_faulty_groups+1)-1))
                else:
                    efforts.append(effort +
                                   j*((len(uuts)+1)/(curr_faults[1]+1)-1))
        if (not found):
            if (collapse):
                effort += group_len - curr_faulty_groups
            else:
                effort += len(uuts) - curr_faults[1]
        else:
            if (collapse):
                k = target + curr_faults[0] - actual
                effort += k*((group_len+1)/(curr_faulty_groups+1)-1)
            else:
                k = target + curr_faults[0] - actual
                effort += k*((len(uuts)+1)/(curr_faults[1]+1)-1)
    if (avg):
        return sum(efforts)/target
    else:
        return effort


def getTie(faults: Dict[int, List[Spectrum.Element]],
           s_iter: Iterator[Scores.Score], spectrum: Spectrum,
           cached: Optional[Scores.Score], worst_effort: bool):
    score = cached if (cached is not None) else next(s_iter)
    s2: Optional[Scores.Score] = score
    uuts = set()
    group_len = 0
    curr_fault_num = 0
    curr_fault_locs = 0
    curr_faulty_groups = 0
    # Get all UUTs with same score
    while (s2 is not None and s2.score == score.score):
        group = find_group(s2.elem, spectrum)
        uuts.update(group)
        group_len += 1
        # Check if fault is in group
        faulty_group = False
        toRemove = set()
        faulty_locs = []
        for item in faults.items():
            worst_toRemove = []
            locs = item[1]
            for loc in locs:
                if (loc in group):
                    if (worst_effort and len(locs) > 1):
                        worst_toRemove.append(loc)
                        continue
                    # print("found fault", item[0])
                    curr_fault_num += 1
                    if (loc not in faulty_locs):
                        faulty_locs.append(loc)
                        curr_fault_locs += 1
                    if (not faulty_group):
                        curr_faulty_groups += 1
                        faulty_group = True
                    # faults.remove(fault)
                    toRemove.add(item[0])
                    break
            if (worst_effort):
                for loc in worst_toRemove:
                    locs.remove(loc)
        for fault in toRemove:
            faults.pop(fault)
        s2 = next(s_iter, None)
    else:
        cached = s2
    return uuts, group_len, [curr_fault_num, curr_fault_locs], \
        curr_faulty_groups, cached
