from typing import List, Dict, Set
from flitsr.score import Scores
from flitsr.spectrum import Spectrum
from flitsr.output import find_group


def one_top1(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
             spectrum: Spectrum):
    uuts = get_top1(scores, spectrum)
    for fault in faults.values():
        for loc in fault:
            if (loc in uuts):
                return True
    return False


def all_top1(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
             spectrum: Spectrum):
    uuts = get_top1(scores, spectrum)
    count = 0
    for fault in faults.values():
        for loc in fault:
            if (loc in uuts):
                count += 1
                break  # Only consider first location of fault
    return (count == len(faults))


def percent_top1(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
                 spectrum: Spectrum):
    if (len(faults) == 0):
        return 100
    else:
        uuts = get_top1(scores, spectrum)
        count = 0
        for fault in faults.values():
            for loc in fault:
                if (loc in uuts):
                    count += 1
                    break
        return (count/len(faults))*100


def size_top1(faults: Dict[int, List[Spectrum.Element]], scores: Scores,
              spectrum: Spectrum):
    uuts = get_top1(scores, spectrum)
    return len(uuts)


# <------------------------- Helper functions ---------------------->


def get_top1(scores: Scores, spectrum: Spectrum):
    s_iter = iter(scores)
    score = next(s_iter)
    uuts: Set[Spectrum.Element] = set()
    uuts.update(find_group(score.elem, spectrum))
    # Get all UUTs with same score
    while ((s2 := next(s_iter, None)) and s2.score == score.score):
        # print(i, sort[i][1])
        uuts.update(find_group(s2.elem, spectrum))
    return uuts
