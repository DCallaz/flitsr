# PYTHON_ARGCOMPLETE_OK
from itertools import permutations
import math
from fractions import Fraction
import argparse
from typing import Dict, Iterable, Collection, Set, Optional, Callable
from numpy import random, fromiter
import ast
import re
from flitsr.calcs import BUModel

MAX_ITERS = math.factorial(10)


class Randomizer:
    # 10! => 95% confidence in a 0.05% margin of error (unlimited pop.)
    def __init__[T](self, seq: Collection[T], max_iters: int = MAX_ITERS):
        self.seq = seq
        self.max_iters = min(max_iters, math.factorial(len(seq)))
        self.perm_list: Set[Collection[T]] = set()

    def __iter__(self):
        self.perm_list = set()
        return self

    def __next__(self):
        if (len(self.perm_list) < self.max_iters):
            while True:
                arr = fromiter(self.seq, dtype=object, count=len(self.seq))
                curr = tuple(random.permutation(arr))
                if (curr not in self.perm_list):
                    self.perm_list.add(curr)
                    return curr
        else:
            raise StopIteration


class Faults[T]:
    def __init__(self, fs: Dict[T, Collection[int]]):
        self._by_locs = fs
        self._by_faults: Dict[int, Set[T]] = {}
        for loc in fs.keys():
            for fault in fs[loc]:
                self._by_faults.setdefault(fault, set()).add(loc)

    def get_locs(self, fault: int):
        return self._by_faults[fault]

    def get_faults(self, loc: T):
        return self._by_locs[loc]

    def locs(self):
        return self._by_locs.keys()

    def faults(self):
        return self._by_faults.keys()


def type_faults(inp):
    try:
        faults = eval(inp)
    except Exception:
        raise argparse.ArgumentTypeError("Faults must be in the format: "
                                         "{<loc>: [<fault>,...],...}")
    return faults


def exact_method[T](fs: Dict[T, Collection[int]], q: int, elems: Collection[T],
                    weffort=False, x=BUModel.PERFECT()):
    fs = Faults(fs)
    dist: Dict[float, int] = {}
    perms: Iterable
    mtot: int
    if (len(elems) <= 11):
        perms = permutations(elems)
        mtot = math.factorial(len(elems))
    else:
        perms = Randomizer(elems)
        mtot = perms.max_iters
    for rank in perms:
        value = wasted_effort(rank, fs, q, weffort, x=x)
        dist.setdefault(value, 0)
        dist[value] += 1
    return sum(v*c for v, c in dist.items())/mtot


def wasted_effort[T](rank: Iterable[T], fs: Faults[T],
                     k: int, weffort=False,
                     x: BUModel = BUModel.PERFECT()) -> int:
    seen: Set[int] = set()
    seen_locs: Dict[int, Set[T]] = {}
    tot = 0
    for i in rank:
        if (not weffort):
            tot += 1
        if (i in fs.locs()):
            if (x.model is BUModel.PERFECT().model):
                seen.update(fs.get_faults(i))
            elif (x.model is BUModel.INEPT().model):
                for fault in fs.get_faults(i):
                    seen_locs.setdefault(fault, set()).add(i)
                    if (len(seen_locs[fault]) == len(fs.get_locs(fault))):
                        seen.add(fault)
            else:
                for fault in fs.get_faults(i):
                    seen_locs.setdefault(fault, set()).add(i)
                    tot_locs = len(fs.get_locs(fault))
                    if (len(seen_locs[fault]) == min(tot_locs,
                                                     x.strategy(tot_locs))):
                        seen.add(fault)
        elif (weffort):
            tot += 1
        if (len(seen) >= k):
            break
    return tot


def prec_rec[T](rank: Iterable[T], fs: Faults[T], n: int,
                precision=False) -> float:
    seen: Set[int] = set()
    tot: int = 0
    try:
        rank_iter = iter(rank)
        for _ in range(0, n):
            i = next(rank_iter)
            if (i in fs.locs()):
                tot += len(set(fs.get_faults(i)).difference(seen))
                seen.update(fs.get_faults(i))
    except StopIteration:
        pass
    if (precision):
        return tot/n
    else:
        fn = len(fs.faults())
        return tot/fn


def new_method(fs, q, m, weffort=False):
    l = len(fs)
    if (weffort):
        expval = Fraction(m-l, l+1)
    else:
        expval = Fraction(m+1, l+1)
    if (len(set(x for v in fs.values() for x in v)) == 1):
        return expval
    elif (l > 11):
        return q*expval
    dist = {}
    for rank in permutations(range(1, l+1)):
        seen = set()
        tot = 0
        for i in rank:
            tot += 1
            seen.update(fs[i])
            if (len(seen) >= q):
                break
        if (tot not in dist):
            dist[tot] = 0
        dist[tot] += 1
    return expval*Fraction(sum(v*c for v, c in dist.items()),
                           math.factorial(l))


def type_def_strt(inp: str):
    fail = False
    try:
        exp = ast.parse(inp, mode='eval')
        if (isinstance(exp, ast.Expression) and
                re.fullmatch('[l\\d\\s()/+*-]+', inp)):
            return lambda l: eval(inp)
        else:
            fail = True
    except SyntaxError:
        fail = True
    if (fail):
        raise argparse.ArgumentTypeError("Please provide a valid expression "
                                         "containing only the variable `l` "
                                         "and constant digits.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--nth-fault', action='store', type=int, metavar="N",
                        required=True, dest='q',
                        help='Get the expected value for the Nth fault')
    parser.add_argument('-m', '--size', action='store', type=int, metavar="SIZE",
                        required=True, dest='m', help='The size of the ranking')
    parser.add_argument('-f', '--faults', action='store', type=type_faults,
                        required=True, help="The fault groupings. Format is: "
                        "{<loc>: [<fault>,...],...}")
    parser.add_argument('-w', '--wasted-effort', action='store_true',
                        help='Compute the wasted effort instead of the expected '
                        'position in the tie')
    parser.add_argument('-x', '--bug-understanding-model', choices=['PERFECT',
                        'DEFECTIVE', 'INEPT'], help='The bug understanding '
                        'model to use. Note: the default defective strategy '
                        'is l/2, to use a different strategy, see '
                        '`--defective-strategy`.', default='PERFECT')
    parser.add_argument('-s', '--defective-strategy', action='store',
                        help='Specify an alternate strategy to use for '
                        'defective bug understanding.', type=type_def_strt)
    args = parser.parse_args()

    fs = args.faults
    q = args.q
    m = args.m
    we = args.wasted_effort
    if (args.bug_understanding_model == 'DEFECTIVE'):
        x = BUModel[args.bug_understanding_model](args.defective_strategy)
    else:
        x = BUModel[args.bug_understanding_model]()
    print(exact_method(fs, q, range(1, m+1), weffort=we, x=x))
