from suspicious import Suspicious
from spectrum import Spectrum
from typing import List, Tuple
import random

orig = None


def apply_formula(spec: Spectrum, formula: str):
    scores: List[Tuple[Spectrum.Element, float, float]] = []
    for elem in spec.elements:
        sus = Suspicious(spec.f[elem], spec.tf, spec.p[elem], spec.tp)
        exect = spec.p[elem]+spec.f[elem]
        scores.append((sus.execute(formula), elem, exect))
    return scores


def sort(scores, order, tiebrk):
    if (tiebrk == 1):  # Sorted by execution counts
        sort = sorted(scores, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 2):  # random ordering
        random.shuffle(scores)
        sort = sorted(scores, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 3):  # original ranking tie break
        if (orig is not None):  # sort by original ranking then execution count
            sort = sorted(scores, key=lambda x: orig[x[1]][2], reverse=order)
            sort = sorted(sort, key=lambda x: orig[x[1]][0], reverse=order)
        else:  # if no orig, still sort by current execution count
            sort = sorted(scores, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
    else:
        sort = sorted(scores, key=lambda x: x[0], reverse=order)
    return sort


def localize(spectrum, formula, tiebrk, order=True):
    """
    Calculate the scores for each of the elements using the given formula.
    Assumes a non-empty spectrum.
    """
    scores = apply_formula(spectrum, formula)
    return sort(scores, order, tiebrk)
