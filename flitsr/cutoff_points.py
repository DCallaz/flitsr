from flitsr.suspicious import Suspicious
from flitsr.ranking import Ranking, Rank
from flitsr.spectrum import Spectrum
from typing import List, Dict, Any


def basis(basis_num: int, spectrum: Spectrum,
          faults: Dict[int, List[Spectrum.Element]], ranking: Ranking,
          formula: str, effort: str) -> Ranking:
    new_ranking: Ranking = Ranking()
    r_iter = iter(ranking)
    rank = next(r_iter, None)
    first_fault = -1
    seen_basis = 0
    while (rank is not None and (seen_basis < basis_num or
                                 first_fault == -1)):
        temp_items: List[Rank] = []
        next_rank = rank
        while (next_rank is not None and next_rank.score == rank.score):
            if (first_fault == -1 and any(next_rank.elem in fault_locs for
                                          fault_locs in faults.values())):
                first_fault = len(temp_items)
            temp_items.append(next_rank)
            next_rank = next(r_iter, None)
        if (effort == 'worst' or first_fault == -1):
            new_ranking.extend(temp_items)
        elif (effort == 'best'):
            new_ranking.extend(temp_items[:first_fault+1])
        elif (effort == 'resolve'):
            new_ranking.extend([temp_items[first_fault]])
        if (next_rank is not None and rank.score-1 != next_rank.score):
            seen_basis += 1
        rank = next_rank
    return new_ranking


def oba(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
        ranking: Ranking, formula: str, effort: str):
    return method(float('inf'), spectrum, faults, ranking, effort)


def mba_dominator(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                  ranking: Ranking, formula: str, effort: str):
    sus = Suspicious(spectrum.tf, spectrum.tf, spectrum.tp, spectrum.tp)
    score = sus.execute(formula)
    return method(score, spectrum, faults, ranking, effort)


def mba_zombie(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
               ranking: Ranking, formula: str, effort: str):
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    score = sus.execute(formula)
    return method(score, spectrum, faults, ranking, effort)


def mba_5_perc(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
               ranking: Ranking, formula: str, effort: str):
    size = 0
    for group in spectrum.groups():
        size += len(group.get_elements())
    return method(int(size*0.05), spectrum, faults, ranking, effort, True)


def mba_10_perc(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                ranking: Ranking, formula: str, effort: str):
    size = 0
    for group in spectrum.groups():
        size += len(group.get_elements())
    return method(int(size*0.1), spectrum, faults, ranking, effort, True)


def mba_const_add(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                  ranking: Ranking, formula: str, effort: str):
    tot_size = 0
    for group in spectrum.groups():
        tot_size += len(group.get_elements())
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    zero = sus.execute(formula)
    new_ranking = Ranking()
    r_iter = iter(ranking)
    rank = next(r_iter, None)
    stop_i = float('inf')
    f_num = 0
    size = 0
    while (rank is not None and size+1 <= stop_i and (rank.score > zero or
                                                      f_num == 0)):
        next_rank = rank
        fault_num = 0
        while (next_rank is not None and (next_rank.score == rank.score)):
            if (any(next_rank.elem in fault_locs for fault_locs in
                    faults.values())):
                fault_num += 1
            new_ranking.extend([next_rank])
            size += len(next_rank.group.get_elements())
            next_rank = next(r_iter, None)
        if (fault_num != 0):  # should've stopped already: size <= stop_i
            # recalculate stop amount
            f_num += fault_num
            stop_i = size + tot_size*0.01
        rank = next_rank
    return new_ranking


def mba_optimal(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
                ranking: Ranking, formula: str, effort: str):
    sus = Suspicious(0, spectrum.tf, 0, spectrum.tp)
    zero = sus.execute(formula)
    new_ranking = Ranking()
    r_iter = iter(ranking)
    rank = next(r_iter, None)
    stop_i = float('inf')
    f_num = 0
    size = 0
    while (rank is not None and size+1 <= stop_i and (rank.score > zero or
                                                      f_num == 0)):
        next_rank = rank
        fault_num = 0
        while (next_rank is not None and (next_rank.score == rank.score)):
            if (any(next_rank.elem in fault_locs for fault_locs in
                    faults.values())):
                fault_num += 1
            new_ranking.extend([next_rank])
            size += len(next_rank.group.get_elements())
            next_rank = next(r_iter, None)
        if (fault_num != 0):  # should've stopped already: size <= stop_i
            # recalculate stop amount
            f_num += fault_num
            stop_i = size + size/(f_num+1)
        rank = next_rank
    return new_ranking


def aba(spectrum: Spectrum, faults: Dict[int, List[Spectrum.Element]],
        ranking: Ranking, formula: str, effort: str):
    new_ranking = Ranking()
    r_iter = iter(ranking)
    rank = next(r_iter, None)
    temp_ranking: List[Rank] = []
    while (rank is not None and rank.score > 0.0):
        fault = False
        next_rank = rank
        while (next_rank is not None and next_rank.score == rank.score):
            if (any(next_rank.elem in fault_locs for fault_locs in
                    faults.values())):
                fault = True
            temp_ranking.append(next_rank)
            next_rank = next(r_iter, None)
        if (fault):
            new_ranking.extend(temp_ranking)
            temp_ranking.clear()
        rank = next_rank
    return new_ranking


def method(stop_score: float, spectrum: Spectrum,
           faults: Dict[int, List[Spectrum.Element]], ranking: Ranking,
           effort: str, by_rank=False):
    new_ranking = Ranking()
    r_iter = iter(ranking)
    rank = next(r_iter, None)
    first_fault = -1
    size = 0
    while (rank is not None and
           ((not by_rank and rank.score > stop_score)
            or (by_rank and size < stop_score) or first_fault == -1)):
        temp_ranking: List[Rank] = []
        next_rank = rank
        while (rank is not None and next_rank.score == rank.score):
            if (first_fault == -1 and any(next_rank.elem in fault_locs for
                                          fault_locs in faults.values())):
                first_fault = len(temp_ranking)
            temp_ranking.append(next_rank)
            size += len(next_rank.group.get_elements())
            next_rank = next(r_iter, None)
        if (effort == 'worst' or rank.score > stop_score or first_fault == -1):
            new_ranking.extend(temp_ranking)
        elif (effort == 2):
            new_ranking.extend(temp_ranking[:first_fault+1])
        else:
            new_ranking.extend([temp_ranking[first_fault]])
        rank = next_rank
    return new_ranking


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
        ranking: Ranking, formula: str, effort: str):
    # get the function
    func = funcs[cutoff]
    return func(spectrum, faults, ranking, formula, effort)
