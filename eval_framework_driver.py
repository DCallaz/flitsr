# PYTHON_ARGCOMPLETE_OK
from argparse import ArgumentParser, ArgumentTypeError
from enum import Enum, auto
from numpy import random
from typing import Set, Dict, List, Optional, Collection, Tuple, Union, \
        overload, Iterable
from perms import exact_method, type_faults, type_def_strt
from flitsr.tie import Ties, Tie, comb
from flitsr.ranking import Ranking, Rankings
from flitsr.spectrum import Spectrum
from flitsr.calcs import BUModel
from itertools import combinations, chain, product
from collections import Counter
from datetime import timedelta
import sys
import re
import time


class Calc(Enum):
    PRECISION = auto()
    RECALL = auto()
    WEFFORT = auto()
    EXAM = auto()


def get_overlaps(m: int, f: int, l_max: int, o: int, rng):
    if (o == 0):
        return []
    elif (f == 1 or min(l_max, m)*(f-1) < o):
        raise ValueError(f"Cannot have {o} overlaps for {f} faults with "
                         f"{l_max} locations each (with {m} total locations)")
    overlap = None
    while (overlap is None or not all(c <= l_max for c in ovlp_cnt(overlap))
           or len(overlap)+f-len(set(i for o in overlap for i in o)) > m):
        overlap = []
        o_tot = 0
        while (o_tot < o):
            n = min(2 + rng.poisson(0.2), o-o_tot+1, f)  # num. faults in ovrlp
            overlap.append(tuple(rng.choice(range(1, f+1), n, replace=False)))
            o_tot += n-1
    return overlap


@overload
def ovlp_cnt(overlaps: List[Tuple[int]]) -> List[int]: ...


@overload
def ovlp_cnt(overlaps: List[Tuple[int]], ind: int) -> int: ...


def ovlp_cnt(overlaps: List[Tuple[int]],
             ind: Optional[int] = None) -> Union[List[int], int]:
    cnt = Counter([j for i in overlaps for j in i])
    if (ind):
        return cnt[ind]
    else:
        return list(cnt.values())


def experiment[T](m: int, f: int, l_max: int, o: int, q: int, calc: Calc,
                  x: BUModel, fs: Optional[Dict[int, Set[int]]] = None):
    """
    Runs an experiment with the given parameters.

    Args:
      m: The number of elements in the tie.
      f: The number of faults in the tie.
      l_max: The maximum number of elements per fault. The number of faulty
        elements per fault is sampled randomly from the range [0, l_max].
      o: The total number of overlapping elements.
      q: The inspection limit. Either the number of faults to find (if wasted
      effort), or the number of elements to inspect (if precision/recall).
      calc: The type of calculation to perform.
    """
    if (f-o > m):
        raise ValueError(f"Cannot have {f} faults in {m} locations with {o} "
                         f"overlaps (not enough locations!)")
    # create the elements
    elems = set(range(1, m+1))

    # restrict q
    q = min(f, q)

    # sample the fault locations
    if (fs is None):
        rng = random.default_rng()
        fs = {}
        f_locs: Dict[int, Set[int]] = {}
        selected: Set[int] = set()
        overlaps = get_overlaps(m, f, l_max, o, rng)
        # get the number of fault locations for each fault
        while True:
            f_num_loc = rng.integers(low=1, high=(l_max+1), size=f)
            f_num_loc = [max(0, n-ovlp_cnt(overlaps, i)) for i, n in
                         enumerate(f_num_loc, start=1)]
            if (sum(f_num_loc)+len(overlaps) <= m):
                break
        # get non-overlaps first
        for i in range(1, f+1):
            no = ovlp_cnt(overlaps, i)  # num. overlaps for this fault
            if (no == l_max):  # only overlaps for this fault
                continue
            ls = f_num_loc[i-1]
            choices = list(rng.choice(list(elems.difference(selected)),
                                      size=(ls), replace=False))
            # print(i, no, ls, choices)
            selected.update(choices)
            f_locs.setdefault(i, set()).update(choices)
            for choice in choices:
                fs.setdefault(choice, set()).add(i)
        # now get overlaps
        for ovlp in overlaps:
            o_elem = rng.choice(list(elems.difference(selected)))
            selected.add(o_elem)
            fs.setdefault(o_elem, set()).update(ovlp)
    e_start = time.time()
    exact = exact_method(fs, q, elems, weffort=True, x=x)  # type: ignore
    e_end = time.time()
    tie = construct_tie(elems, fs)
    f_start = time.time()
    formula = tie.expected_value(q, weffort=True, x=x)
    f_end = time.time()
    return exact, formula, fs, (e_end-e_start), (f_end-f_start)


def mfault_mloc_prob(fs: Dict[int, Set[int]], k: int, p: int):
    l = len(set().union(*fs.values()))
    numerator = comb(l, p)
    num_str = f'{numerator}'
    for i in range(k-1, 0, -1):
        factor = comb(len(fs) - (i+1), (k-1) - i)
        num_str += f' {factor}*('
        for subset in combinations(fs.keys(), i):
            non_chosen = set().union(*[fs[f] for f in fs if f not in subset])
            subset_no_ovrlp = (set().union(*[fs[f] for f in subset])
                               .difference(non_chosen))
            cur = comb(len(subset_no_ovrlp), p)
            numerator += factor * (-1)**(k-i) * cur
            num_str += f' {"-" if (k-i) % 2 == 1 else "+"} {cur}'
        num_str += ')'
    print(num_str)
    return numerator/comb(l, p)


def construct_tie(elems: Collection[int], fs: Dict[int, Set[int]]):
    r = Ranking()
    spec_elems = []
    faults: Dict[int, Set[Spectrum.Element]] = {}
    for e in elems:
        spec_elem = Spectrum.Element([f'u{e}'], e, list(fs.get(e, [])))
        spec_elems.append(spec_elem)
        for fault in fs.get(e, []):
            faults.setdefault(fault, set()).add(spec_elem)
        r.append(spec_elem, 1.0, 1)
    rs = Rankings(faults, spec_elems, [r])
    ts = Ties(rs)
    return ts[0]


def intRange(inp: str):
    rng_str = "\\[\\s*(\\d+)\\s*(?:,\\s*(\\d+)\\s*(?:,\\s*(\\d+)\\s*)?)?\\]"
    m = re.fullmatch(f"(?:{rng_str})+", inp)
    if (not m):
        raise ArgumentTypeError("Please provide a list of ranges in the form: "
                                "\"\\[<start>,[<stop>[,<step>]]\\]\"")
    rngs: List[Iterable] = []
    for m in re.finditer(rng_str, inp):
        if (m.group(3)):
            rngs.append(range(int(m.group(1)), int(m.group(2)),
                              int(m.group(3))))
        elif (m.group(2)):
            rngs.append(range(int(m.group(1)), int(m.group(2))))
        else:
            rngs.append([int(m.group(1))])
    return list(chain(*rngs))


def sfdiv(n, d):
    if (n == 0.0):
        return 0.0
    else:
        return n/d


def exp_iter(args):
    print('Setup:', f'm={args.m}, f={args.f}, '
          f'l={args.l_max}, o={args.o}, q={args.q}')
    if (args.bug_understanding_model == 'DEFECTIVE'):
        x = BUModel[args.bug_understanding_model](args.defective_strategy)
    else:
        x = BUModel[args.bug_understanding_model]()
    for m, f, l, o, q in product(args.m, args.f, args.l_max, args.o, args.q):
        if (q > f or (f == 1 and o > 0) or min(l, m)*(f-1) < o or f-o > m or
            l > m or f > m):
            continue
        print(f'm={m}, f={f}, l={l}, o={o}, q={q}')
        try:
            for i in range(args.iterations):
                exact, formula, fs, e_dur, \
                        f_dur = experiment(m, f, l, o, q, Calc.WEFFORT,
                                           x=x, fs=args.faults)
                ft = timedelta(seconds=f_dur)
                et = timedelta(seconds=e_dur)
                if (sfdiv(abs(exact - formula), exact) > 5e-2):
                    print(f'FAILED {formula} != {exact} [{ft};{et}] ({fs})')
                else:
                    print(f'Passed {formula} = {exact} [{ft};{et}] ({fs})')
        except ValueError as e:
            print(f'Skipping invalid configuration ({e})...')


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-m', action='store', required=True, type=intRange,
                        help='The number of elements in the tie')
    parser.add_argument('-f', action='store', required=True, type=intRange,
                        help='The number of faults in the tie')
    parser.add_argument('-l', '--l-max', action='store', required=True,
                        type=intRange, help='The maximum number of locations '
                        'per fault in the tie')
    parser.add_argument('-q', action='store', required=True, type=intRange,
                        help='The inspection cut-off point.')
    parser.add_argument('-o', '--overlap', action='store', default='0',
                        type=intRange, help='The total number of overlapping '
                        'elements allowed.', dest='o')
    parser.add_argument('-b', '--faults', action='store', type=type_faults,
                        default=None, help="The fault groupings. Format is: "
                        "{<loc>: [<fault>,...],...}")
    parser.add_argument('-i', '--iterations', action='store', type=int, default=1,
                        help='The number of iterations per experiment to run.')
    parser.add_argument('-x', '--bug-understanding-model', choices=['PERFECT',
                        'DEFECTIVE', 'INEPT'], help='The bug understanding '
                        'model to use. Note: the default defective strategy '
                        'is l/2, to use a different strategy, see '
                        '`--defective-strategy`.', default='PERFECT')
    parser.add_argument('-s', '--defective-strategy', action='store',
                        help='Specify an alternate strategy to use for '
                        'defective bug understanding.', type=type_def_strt)
    args = parser.parse_args()
    exp_iter(args)
