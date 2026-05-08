# PYTHON_ARGCOMPLETE_OK
from itertools import permutations
import math
from enum import Enum, auto
from fractions import Fraction
import argparse
from argparse import ArgumentTypeError
from typing import Dict, Iterable, Collection, Set, Any, TypeVar, Generic
from numpy import random, fromiter
import ast
import re
from flitsr.calculations import BUModel
from functools import partial

T = TypeVar('T')

MAX_ITERS = math.factorial(10)


class Calc(Enum):
    PRECISION = auto()
    RECALL = auto()
    WEFFORT = auto()
    EXAM = auto()

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s: str):
        if (not hasattr(Calc, s)):
            raise ArgumentTypeError(f'Invalid calculation {s}')
        return getattr(Calc, s)


class Randomizer(Generic[T]):
    # 10! => 95% confidence in a 0.05% margin of error (unlimited pop.)
    def __init__(self, seq: Collection[T], max_iters: int = MAX_ITERS):
        self.seq = seq
        self.max_iters = min(max_iters, math.factorial(len(seq)))
        # only store permutations (for de-duplication) if not so big
        self.store = len(seq) < 100
        self.perm_list: Set[Collection[T]] = set()
        self.perms = 0

    def __iter__(self):
        self.perm_list = set()
        self.perms = 0
        return self

    def __next__(self):
        if (self.perms < self.max_iters):
            while True:
                arr = fromiter(self.seq, dtype=object, count=len(self.seq))
                curr = tuple(random.permutation(arr))
                if (self.store):
                    if (curr in self.perm_list):
                        continue
                    else:
                        self.perm_list.add(curr)
                self.perms += 1
                return curr
        else:
            raise StopIteration


class Faults(Generic[T]):
    def __init__(self, fs: Dict[T, Collection[Any]]):
        self._by_locs = fs
        self._by_faults: Dict[Any, Set[T]] = {}
        for loc in fs.keys():
            for fault in fs[loc]:
                self._by_faults.setdefault(fault, set()).add(loc)

    def get_locs(self, fault: Any):
        return self._by_faults[fault]

    def get_faults(self, loc: T):
        return self._by_locs[loc]

    def get_by_faults(self) -> Dict[int, Set[T]]:
        return self._by_faults.copy()

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


def get_func(calc: Calc):
    if (calc is Calc.WEFFORT):
        return partial(wasted_effort, weffort=True)
    elif (calc is Calc.EXAM):
        return partial(wasted_effort, weffort=False)
    elif (calc is Calc.RECALL):
        return partial(prec_rec, precision=False)
    elif (calc is Calc.PRECISION):
        return partial(prec_rec, precision=True)


def exact_method(fs: Dict[T, Collection[int]], q: int, elems: Collection[T],
                 calc: Calc, bu=BUModel.PERFECT):
    fs = Faults(fs)
    x = bu.get_dict(fs.get_by_faults())
    dist: Dict[float, int] = {}
    perms: Iterable
    mtot: int
    func = get_func(calc)
    if (len(elems) <= 11):
        perms = permutations(elems)
        mtot = math.factorial(len(elems))
    else:
        perms = Randomizer(elems)
        mtot = perms.max_iters
    for rank in perms:
        value = func(rank, fs, q, x)
        dist.setdefault(value, 0)
        dist[value] += 1
    return sum(v*c for v, c in dist.items())/mtot


def wasted_effort(rank: Iterable[T], fs: Faults[T], k: int,
                  x: Dict[Any, int], weffort=False) -> int:
    to_inspect = x.copy()
    seen: Set[int] = set()
    tot = 0
    for i in rank:
        if (not weffort):
            tot += 1
        if (i in fs.locs()):
            for fault in fs.get_faults(i):
                to_inspect[fault] -= 1
                if (to_inspect[fault] == 0):
                    seen.add(fault)
        elif (weffort):
            tot += 1
        if (len(seen) >= k):
            break
    return tot


def prec_rec(rank: Iterable[T], fs: Faults[T], n: int,
             x: Dict[Any, int], precision=False) -> float:
    to_inspect = x.copy()
    seen: Set[int] = set()
    try:
        rank_iter = iter(rank)
        for _ in range(0, n):
            i = next(rank_iter)
            if (i in fs.locs()):
                for fault in fs.get_faults(i):
                    to_inspect[fault] -= 1
                    if (to_inspect[fault] == 0):
                        seen.add(fault)
    except StopIteration:
        pass
    if (precision):
        return len(seen)/n
    else:
        fn = len(fs.faults())
        return len(seen)/fn


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
    parser.add_argument('-c', '--calculation', choices=list(Calc),
                        type=Calc.from_string, default=Calc.WEFFORT,
                        help='Specifies the calculation to perform (default '
                        'Wasted Effort)')
    parser.add_argument('-x', '--bug-understanding', type=BUModel.from_string,
                        choices=BUModel.get_types(), help='The bug '
                        'understanding model to use. Note: the default '
                        'defective strategy is l/2, to use a different '
                        'strategy, see `--defective-strategy`.',
                        default=BUModel.PERFECT)
    parser.add_argument('-s', '--defective-strategy', action='store',
                        help='Specify an alternate strategy to use for '
                        'defective bug understanding.', type=type_def_strt)
    args = parser.parse_args()

    fs = args.faults
    q = args.q
    m = args.m
    if (args.bug_understanding == 'DEFECTIVE' and
            args.defective_strategy):
        args.bug_understanding = BUModel(BUModel.DEFECTIVE,
                                         args.defective_strategy)
    print(exact_method(fs, q, range(1, m+1), calc=args.calculation,
                       bu=args.bug_understanding))
