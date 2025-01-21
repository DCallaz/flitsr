from flitsr.suspicious import Suspicious
from flitsr.score import Scores
from flitsr.spectrum import Spectrum
from typing import List, Dict, Any


def basis(basis_num: int, spectrum: Spectrum,
          faults: Dict[int, List[Spectrum.Element]], scores: Scores,
          formula: str, effort: str) -> Scores:
    new_scores: Scores = Scores()
    s_iter = iter(scores)
    score = next(s_iter, None)
    first_fault = -1
    seen_basis = 0
    while (score is not None and (seen_basis < basis_num or
                                  first_fault == -1)):
        temp_items: List[Scores.Score] = []
        next_score = score
        while (next_score is not None and next_score.score == score.score):
            if (first_fault == -1 and any(next_score.elem in fault_locs for
                                          fault_locs in faults.values())):
                first_fault = len(temp_items)
            temp_items.append(next_score)
            next_score = next(s_iter, None)
        if (effort == 'worst' or first_fault == -1):
            new_scores.extend(temp_items)
        elif (effort == 'best'):
            new_scores.extend(temp_items[:first_fault+1])
        elif (effort == 'resolve'):
            new_scores.extend([temp_items[first_fault]])
        if (next_score is not None and score.score-1 != next_score.score):
            seen_basis += 1
        score = next_score
    return new_scores


def oba(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
        scores: Scores, formula: str, effort: str):
    return method(float('inf'), spectrum, faults, scores, effort)


def mba_dominator(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                  scores: Scores, formula: str, effort: str):
    sus = Suspicious(spectrum.tf, spectrum.tf, spectrum.tp, spectrum.tp)
    score = sus.execute(formula)
    return method(score, spectrum, faults, scores, effort)


def mba_zombie(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
               scores: Scores, formula: str, effort: str):
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    score = sus.execute(formula)
    return method(score, spectrum, faults, scores, effort)


def mba_5_perc(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
               scores: Scores, formula: str, effort: str):
    size = 0
    for group in spectrum.groups():
        size += len(group.get_elements())
    return method(int(size*0.05), spectrum, faults, scores, effort, True)


def mba_10_perc(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                scores: Scores, formula: str, effort: str):
    size = 0
    for group in spectrum.groups():
        size += len(group.get_elements())
    return method(int(size*0.1), spectrum, faults, scores, effort, True)


def mba_const_add(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                  scores: Scores, formula: str, effort: str):
    tot_size = 0
    for group in spectrum.groups():
        tot_size += len(group.get_elements())
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    zero = sus.execute(formula)
    new_scores = Scores()
    s_iter = iter(scores)
    score = next(s_iter, None)
    stop_i = float('inf')
    f_num = 0
    size = 0
    while (score is not None and size+1 <= stop_i and (score.score > zero or
                                                       f_num == 0)):
        next_score = score
        fault_num = 0
        while (next_score is not None and (next_score.score == score.score)):
            if (any(next_score.elem in fault_locs for fault_locs in
                    faults.values())):
                fault_num += 1
            new_scores.extend([next_score])
            size += len(next_score.group.get_elements())
            next_score = next(s_iter, None)
        if (fault_num != 0):  # should've stopped already: size <= stop_i
            # recalculate stop amount
            f_num += fault_num
            stop_i = size + tot_size*0.01
        score = next_score
    return new_scores


def mba_optimal(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                scores: Scores, formula: str, effort: str):
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    zero = sus.execute(formula)
    new_scores = Scores()
    s_iter = iter(scores)
    score = next(s_iter, None)
    stop_i = float('inf')
    f_num = 0
    size = 0
    while (score is not None and size+1 <= stop_i and (score.score > zero or
                                                       f_num == 0)):
        next_score = score
        fault_num = 0
        while (next_score is not None and (next_score.score == score.score)):
            if (any(next_score.elem in fault_locs for fault_locs in
                    faults.values())):
                fault_num += 1
            new_scores.extend([next_score])
            size += len(next_score.group.get_elements())
            next_score = next(s_iter, None)
        if (fault_num != 0):  # should've stopped already: size <= stop_i
            # recalculate stop amount
            f_num += fault_num
            stop_i = size + size/(f_num+1)
        score = next_score
    return new_scores


def aba(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
        scores: Scores, formula: str, effort: str):
    new_scores = Scores()
    s_iter = iter(scores)
    score = next(s_iter, None)
    temp_scores: List[Scores.Score] = []
    while (score is not None and score.score > 0.0):
        fault = False
        next_score = score
        while (next_score is not None and next_score.score == score.score):
            if (any(next_score.elem in fault_locs for fault_locs in
                    faults.values())):
                fault = True
            temp_scores.append(next_score)
            next_score = next(s_iter, None)
        if (fault):
            new_scores.extend(temp_scores)
            temp_scores.clear()
        score = next_score
    return new_scores


def method(stop_score: float, spectrum: Spectrum,
           faults: Dict[int, List[Spectrum.Element]], scores: Scores,
           effort: str, rank=False):
    new_scores = Scores()
    s_iter = iter(scores)
    score = next(s_iter, None)
    first_fault = -1
    size = 0
    while (score is not None and
           ((not rank and score.score > stop_score)
            or (rank and size < stop_score) or first_fault == -1)):
        temp_scores: List[Scores.Score] = []
        next_score = score
        while (score is not None and next_score.score == score.score):
            if (first_fault == -1 and any(next_score.elem in fault_locs for
                                          fault_locs in faults.values())):
                first_fault = len(temp_scores)
            temp_scores.append(next_score)
            size += len(next_score.group.get_elements())
            next_score = next(s_iter, None)
        if (effort == 'worst' or score.score > stop_score or first_fault == -1):
            new_scores.extend(temp_scores)
        elif (effort == 2):
            new_scores.extend(temp_scores[:first_fault+1])
        else:
            new_scores.extend([temp_scores[first_fault]])
        score = next_score
    return new_scores


# Populate the function names
funcs: Dict[str, Any] = {}
funcs.update([(name, func) for (name, func) in locals().items() if
              callable(func) and func.__module__ == __name__])


def getNames():
    all_names = funcs.keys()
    names = [x for x in all_names if (not x.startswith("__")
             and x != "cut" and x != "getNames" and x != "method")]
    return names


def cut(cutoff, spectrum, faults: Dict[int, List[Spectrum.Element]],
        scores: Scores, formula: str, effort: str):
    # get the function
    func = funcs[cutoff]
    return func(spectrum, faults, scores, formula, effort)
