from fractions import Fraction
from math import comb
from itertools import combinations
from typing import Any, Set, Dict, Union, Callable, Optional
from flitsr.tie import Tie, Ties
from flitsr.spectrum import Spectrum
AnyEntitiesDict = Union[Dict[Any, Set[Spectrum.Element]],
                        Dict[Any, Set[Spectrum.Entity]]]

# ----------------------------- Effort calculations ---------------------------

# type hint for function computing the expected value for the effort in a tie
Eff_tie_exp = Callable[[Tie, int, bool, bool], float]


def effort_exp_val_tie(tie: Tie, q: int, weffort: bool,
                       collapse=False) -> float:
    """
    Calculates the expected value of the qth fault in the given tie. The
    expected value can either be in terms of wasted effort (not
    counting fault inspection) or actual position in the ranking.

    Args:
      q: The number of faults that need inspection in the tie.
      weffort: Whether to count fault inspections (False) or not (True).
      collapse: By default, the number of elements is counted, if this
        option is given, the number of ambiguity groups is counted instead.
    """
    if (tie.num_faults() == 1):  # single-fault shortcut
        # assert (_single_fault_exp_value(tie, q, weffort, collapse) ==
        #         _multi_fault_exp_value(tie, q, weffort, collapse))
        return _single_fault_exp_value(tie, q, weffort, collapse)
    elif ((all(len(ls) == 1 for ls in tie.active_faults().values()) and
           all(len(fs) == 1 for fs in tie.active_fault_locations().values()))):
        # assert (_single_loc_exp_value(tie, q, weffort, collapse) ==
        #         _multi_fault_exp_value(tie, q, weffort, collapse))
        # single-loc shortcut
        return _single_loc_exp_value(tie, q, weffort, collapse)
    else:
        return _multi_fault_exp_value(tie, q, weffort, collapse)


def effort_exp_val(ties: Ties, target: int, weffort: bool, avg=False,
                   collapse=False, tie_exp_func: Eff_tie_exp =
                   effort_exp_val_tie) -> float:
    """
    Calculates the expected value of the nth fault (given by `target`) in the
    ranking given by `ties`. The expected value can either be in terms of
    wasted effort (not counting fault inspection) or actual position in the
    ranking, depending on whether `weffort` is True or False respectively.

    Args:
      ties: The `Ties` object representing the ranking.
      target: The number of faults to inspect up until.
      weffort: Whether to count fault inspections (False) or not (True).
      avg: When True, computes an average of the expected values of all the
        faults up until the target, instead of just the expected value at the
        target.
      collapse: By default, the number of elements is counted, if this
        option is given, the number of ambiguity groups is counted instead.
      tie_exp_func: Supplying this optional argument will use the given
        function to calculate the expected value of the effort in the tie,
        instead of the default calculation.
    """
    found = False
    actual = 0
    effort = 0.0
    efforts = []
    tie_iter = iter(ties)
    while (not found):
        tie = next(tie_iter)
        # print(tie)
        actual += tie.num_faults(active=True)
        found = (actual >= target)
        if (avg):
            for j in range(1, tie.num_faults()+1):
                efforts.append(effort + tie_exp_func(tie, j, weffort, collapse))
        if (not found):
            effort += tie.len(collapse)
            if (weffort):
                effort -= tie.num_fault_locs(collapse)
        else:
            k = target + tie.num_faults(active=True) - actual
            effort += tie_exp_func(tie, k, weffort, collapse)
    if (avg):
        return sum(efforts)/target
    else:
        return effort


def _exp_effort_in_tie(tie: Tie, e_vk: Union[int, Fraction], weffort: bool,
                       collapse=False) -> float:
    l = tie.num_active_fault_locs(collapse)  # noqa
    size = tie.len(collapse)  # size = n (total tie size)
    if (weffort):
        # remove any fault locs from the total num elements
        size -= tie.num_fault_locs(collapse)  # size = n-l (non-faulty elems)
    else:
        size += 1
    exp_val = Fraction(size, l+1)
    return float(exp_val * e_vk)


def _single_fault_exp_value(tie: Tie, q: int, weffort: bool,
                            collapse=False) -> float:
    # print("single fault")
    assert (tie.num_faults() == 1)
    # should be only one key in _active_faults, so just get it (the next)
    x = tie._active_faults[next(iter(tie._active_faults))]
    return _exp_effort_in_tie(tie, x, weffort, collapse)


def _single_loc_exp_value(tie: Tie, q: int, weffort: bool,
                          collapse=False) -> float:
    # print("single loc")
    l = tie.num_active_fault_locs(collapse)  # noqa
    assert (tie.num_faults() == l)
    return _exp_effort_in_tie(tie, q, weffort, collapse)


def _multi_fault_exp_value(tie: Tie, q: int, weffort: bool,
                           collapse=False) -> float:
    # print("multi fault")
    l = tie.num_active_fault_locs(collapse)  # noqa
    nums = tie.fault_identify_nums(collapse)
    locs = tie.active_faults(collapse)
    k = min(q, tie.num_faults())
    if (all(num == 1 for num in nums.values())):  # perfect BU
        e_vk = _eff_perfect_bu(tie.active_faults(collapse), l, k)
    elif (all(nums[f] == len(locs[f]) for f in nums.keys())):  # inept BU
        e_vk = _eff_inept_bu(tie.active_faults(collapse), l, k)
    else:  # imperfect BU
        e_vk = _eff_imperfect_bu(tie.active_faults(collapse), l, k,
                                 tie._active_faults)
    return _exp_effort_in_tie(tie, e_vk, weffort, collapse)


def _eff_perfect_bu(fs: AnyEntitiesDict, l: int, k: int) -> Fraction:  # noqa
    res = Fraction(l+1)
    for i in range(1, l+1):  # iterate over each fault loc
        numerator = comb(l, i)
        # num_str = f'{numerator}'
        for j in range(k-1, 0, -1):  # iterate over number of faults found
            factor = comb(len(fs) - (j+1), (k-1) - j)
            # num_str += f' {factor}*('
            # iterate over selection
            for subset in combinations(fs.keys(), j):
                non_chosen = set().union(*[fs[f] for f in fs
                                           if f not in subset])
                subset_no_ovrlp = (set().union(*[fs[f] for f in subset])
                                   .difference(non_chosen))
                cur = comb(len(subset_no_ovrlp), i)
                numerator += factor * (-1)**(k-j) * cur
                # num_str += f' {"-" if (k-j) % 2 == 1 else "+"} {cur}'
            # num_str += ')'
        # print(f"({num_str})/{comb(l, i)} = "
        #       f"{Fraction(numerator, comb(l, i))}")
        res -= Fraction(numerator, comb(l, i))
    return res


def _eff_inept_bu(fs: AnyEntitiesDict, l: int, k: int) -> Fraction:  # noqa
    res = Fraction(l+1)
    for i in range(1, l+1):  # iterate over each fault loc
        numerator = 0
        # num_str = f'{numerator}'
        # iterate over number of faults found
        for size_k in range(k, len(fs)+1):
            factor = comb(size_k-1, k-1)
            # num_str += f' {"-" if (size_k-k) % 2 == 1 else "+"} {factor}*('
            # iterate over selection
            for subset in combinations(fs.values(), size_k):
                size = len(set().union(*subset))
                cur = comb(l - size, l - i)
                numerator += (-1)**(size_k-k) * factor * cur
                # num_str += f' + {cur}'
            # num_str += ')'
        # print(f"{i}: ({num_str})/{comb(l, i)} = "
        #       f"{Fraction(numerator, comb(l, i))}")
        res -= Fraction(numerator, comb(l, i))
    return res


def _eff_imperfect_bu(fs: AnyEntitiesDict, l: int, k: int,  # noqa
                  nums: Dict[Any, int]) -> Fraction:
    # l = len(set().union(*fs.values()))
    # numerator = 0
    # num_str = f'{numerator}'
    # # iterate over number of faults found
    # for size_k in range(k, len(fs)+1):
    #     factor = comb(size_k-1, k-1)
    #     num_str += f' {"-" if (size_k-k) % 2 == 1 else "+"} {factor}*('
    #     # iterate over selection
    #     for subset in combinations(fs.keys(), size_k):
    #         cur = 1
    #         sum_xi = 0
    #         cur_str = ''
    #         for fault in subset:
    #             xi = x.strategy(len(fs[fault]))
    #             cur *= comb(len(fs[fault]), xi)
    #             cur_str += f'{comb(len(fs[fault]), xi)}*'
    #             sum_xi += xi
    #         numerator += ((-1)**(size_k-k) * factor * cur *
    #                       comb(l-sum_xi, l-i))
    #         num_str += f' + {cur_str}{comb(l-sum_xi, l-i)}'
    #     num_str += ')'
    # print(f"{i}: ({num_str})/{comb(l, i)} = "
    #       f"{Fraction(numerator, comb(l, i))}")
    # return Fraction(numerator, comb(l, i))
    x_avg = sum(nums.values())/len(nums)
    return Fraction(x_avg * k)

# ---------------------------- Cut-off calculations ---------------------------


def cut_off_exp_val(ties: Ties, target: int, collapse: bool = False) -> float:
    """
    Calculate the expected number of faults found when randomly inspecting the
    first `target` elements of the ranking given by `ties`.

    Args:
      ties: The `Ties` object representing the ranking.
      target: The number of elements to inspect up until.
      collapse: By default, the number of elements is counted, if this
        option is given, the number of ambiguity groups is counted instead.
    """
    tie_iter = iter(ties)
    total = 0
    fault_num = 0.0
    try:
        while (total < target):
            tie = next(tie_iter)
            p = min(target - total, tie.len(collapse))
            # add the expected # of faults found in p
            fault_num += cut_off_exp_val_tie(tie, p, collapse)
            total += p
    except StopIteration:
        pass
    return fault_num


def cut_off_exp_val_tie(tie: Tie, p: int, collapse: bool = False) -> float:
    """
    Calculate the expected number of faults found when randomly inspecting the
    first `p` elements of the tie.

    Args:
      tie: The tie to inspect.
      p: The number of statements to inspect in tie.
      collapse: Whether the count the number of statements or ambiguity groups.
    """
    n = tie.len(collapse)  # total num of statements in the tie
    # short-cut for cut-off not in this tie
    if (p >= n):
        return tie.num_faults(active=True)
    faults = tie.active_faults(collapse)
    tot_found = 0.0
    # sum the expected values of finding each fault
    for f in faults:
        l_bi = len(faults[f])
        u_bi = tie.fault_identify_num(f, collapse)
        if (u_bi == 1):  # perfect BU
            e_I_bi = _cut_perfect_bu(n, l_bi, p)
        elif (u_bi == l_bi):  # inept BU
            e_I_bi = _cut_inept_bu(n, l_bi, p)
        else:  # imperfect BU
            e_I_bi = _cut_imperfect_bu(n, l_bi, p, u_bi)
        tot_found += e_I_bi
    return float(tot_found)


def _cut_perfect_bu(n: int, l_bi: int, xs: int) -> Fraction:
    # Expected value of each fault is {1, 0} <=> probability
    # P(selecting one or more locations of this fault)
    # <=> 1 - P(selecting no locations of this fault)
    return 1 - Fraction(comb(n-l_bi, xs), comb(n, xs))


def _cut_inept_bu(n: int, l_bi: int, xs: int) -> Fraction:
    return Fraction(comb(n - l_bi, n - xs), comb(n, xs))


def _cut_imperfect_bu(n: int, l_bi: int, xs: int, u_bi: int) -> Fraction:
    e_I_bi = Fraction(0)
    for j in range(u_bi, l_bi+1):
        if (xs - j < 0):
            continue
        e_I_bi += Fraction(comb(n - l_bi, xs - j) * comb(l_bi, j), comb(n, xs))
    return e_I_bi
