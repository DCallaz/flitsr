# PYTHON_ARGCOMPLETE_OK
from argparse import ArgumentParser, ArgumentTypeError, ArgumentError
from numpy import random
from typing import Set, Dict, List, Optional, Collection, Tuple, Union, \
        overload, Iterable
from math import comb
from flitsr.tie import Ties, Tie
from flitsr.calculations.perms import exact_method, type_faults, \
        type_def_strt, Calc
from flitsr.calculations.exp_values import effort_exp_val_tie, \
        cut_off_exp_val_tie
from flitsr.ranking import Ranking, Rankings
from flitsr.spectrum import Spectrum
from flitsr.calculations import BUModel
from itertools import combinations, chain, product
from functools import partial
from calc_experiments import Setup, read_exp_file, combine
from collections import Counter
from datetime import timedelta
import sys
import os
import re
import time


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


def get_flitsr_func(calc: Calc):
    if (calc is Calc.WEFFORT):
        return partial(effort_exp_val_tie, weffort=True)
    elif (calc is Calc.EXAM):
        return partial(effort_exp_val_tie, weffort=False)
    elif (calc is Calc.PRECISION):
        def prec(tie: Tie, p: int, collapse: bool):
            return cut_off_exp_val_tie(tie, p, collapse)/p
        return prec
    elif (calc is Calc.RECALL):
        def rec(tie: Tie, p: int, collapse: bool):
            return cut_off_exp_val_tie(tie, p, collapse)/tie.num_faults()
        return rec


def experiment(m: int, f: int, l_max: int, o: int, q: int, calc: Calc,
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
    exact = exact_method(fs, q, elems, calc=calc, bu=x)
    e_end = time.time()
    tie = construct_tie(elems, fs, x)
    func = get_flitsr_func(calc)
    f_start = time.time()
    formula = func(tie, q, collapse=False)
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


def construct_tie(elems: Collection[int], fs: Dict[int, Set[int]],
                  x: BUModel) -> Tie:
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
    ts = Ties(rs, x)
    return ts[0]


def intRange(inp: str):
    if (inp.isdigit()):
        return [int(inp)]
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
    elif (d == 0.0):
        return float('inf')
    else:
        return n/d


def exp_iter(args):
    out = sys.stdout
    exps, setup = None, None
    if (args.output_file is not None):
        if (os.path.isfile(args.output_file) and
                os.stat(args.output_file).st_size != 0):
            # first read in current file
            exps, setup = read_exp_file(args.output_file)
        out = open(args.output_file, 'w')
    cur_setup = Setup(args.m or list(), args.f or list(), args.l_max or list(),
                      args.o or list(), args.q or list())
    exps, setup = combine(exps, setup, None, cur_setup)
    assert (setup is not None)
    if (exps is None):
        exps = dict()
    print(setup, file=out)
    if (args.bug_understanding_model == 'IMPERFECT'):
        x = BUModel(BUModel.IMPERFECT, args.imperfect_strategy)
    else:
        x = args.bug_understanding_model
    for expConfig in setup:
        m, f, l, o, q = (expConfig.m, expConfig.f, expConfig.l, expConfig.o,
                         expConfig.q)
        if ((args.calculation in [Calc.WEFFORT, Calc.EXAM] and q > f) or
            (args.calculation in [Calc.RECALL, Calc.PRECISION] and q > m) or
            (f == 1 and o > 0) or (min(l, m)*(f-1) < o and o > 0)
                or f-o > m or l > m or f > m):
            continue
        print(expConfig, file=out)
        iters = args.iterations
        if (expConfig in exps):
            iters -= len(exps[expConfig])
            print("recovered", expConfig)
            for exp in exps[expConfig]:
                print(exp, file=out)
        try:
            for i in range(iters):
                exact, formula, fs, e_dur, \
                        f_dur = experiment(m, f, l, o, q, args.calculation,
                                           x=x, fs=args.faults)
                ft = timedelta(seconds=f_dur)
                et = timedelta(seconds=e_dur)
                if (sfdiv(abs(exact - formula), exact) > 5e-2):
                    print(f'FAILED {formula} != {exact} [{ft};{et}] ({fs})',
                          file=out)
                else:
                    print(f'Passed {formula} = {exact} [{ft};{et}] ({fs})',
                          file=out)
        except ValueError as e:
            print(f'Skipping invalid configuration ({e})...', file=out)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-m', action='store', default=None, type=intRange,
                        help='The number of elements in the tie')
    parser.add_argument('-f', action='store', default=None, type=intRange,
                        help='The number of faults in the tie')
    parser.add_argument('-l', '--l-max', action='store', default=None,
                        type=intRange, help='The maximum number of locations '
                        'per fault in the tie')
    parser.add_argument('-q', action='store', default=None, type=intRange,
                        help='The inspection cut-off point.')
    parser.add_argument('-o', '--overlap', action='store', default='0',
                        type=intRange, help='The total number of overlapping '
                        'elements allowed.', dest='o')
    parser.add_argument('-b', '--faults', action='store', type=type_faults,
                        default=None, help="The fault groupings. Format is: "
                        "{<loc>: [<fault>,...],...}")
    parser.add_argument('-i', '--iterations', action='store', type=int, default=1,
                        help='The number of iterations per experiment to run.')
    parser.add_argument('-x', '--bug-understanding-model',
                        choices=BUModel.get_types(), type=BUModel.from_string,
                        help='The bug understanding '
                        'model to use. Note: the default imperfect strategy '
                        'is l/2, to use a different strategy, see '
                        '`--imperfect-strategy`.', default=BUModel.PERFECT)
    parser.add_argument('-s', '--imperfect-strategy', action='store',
                        help='Specify an alternate strategy to use for '
                        'imperfect bug understanding.', type=type_def_strt)
    parser.add_argument('-c', '--calculation', choices=list(Calc),
                        type=Calc.from_string, default=Calc.WEFFORT,
                        help='Specifies the calculation to perform (default '
                        'Wasted Effort)')
    parser.add_argument('-p', '--output-file', default=None, action='store',
                        help='Print to the given file (default stdout).')
    args = parser.parse_args()
    # check if something to run
    if ((args.output_file is None or not os.path.isfile(args.output_file) or
         os.stat(args.output_file).st_size == 0) and
            (any(x is None for x in [args.m, args.f, args.l_max, args.q]))):
        reqs_a = []
        for s, v in [('m', args.m), ('f', args.f), ('l', args.l_max),
                     ('q', args.q)]:
            if (v is None):
                reqs_a.append(f'-{s}')
        reqs = ', '.join(reqs_a)
        parser.error('the following arguments are required when '
                     f'no (or empty) input file is given: {reqs}')
    exp_iter(args)
