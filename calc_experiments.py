from datetime import datetime, timedelta
import sys
import re
import time
from ast import literal_eval
from fractions import Fraction
from typing import Dict, Set, Any, List, Optional, NamedTuple, Tuple, Union, \
        Iterator
from functools import total_ordering
from itertools import chain, product
from collections import defaultdict
# from matplotlib import pyplot as plt


@total_ordering
class ExpConfig:
    def __init__(self, m: Union[str, int], f: Union[str, int],
                 l: Union[str, int], o: Union[str, int], q: Union[str, int]):
        if (isinstance(m, str)):
            self.m = int(m)
        else:
            self.m = m
        if (isinstance(f, str)):
            self.f = int(f)
        else:
            self.f = f
        if (isinstance(l, str)):
            self.l = int(l)
        else:
            self.l = l
        if (isinstance(o, str)):
            self.o = int(o)
        else:
            self.o = o
        if (isinstance(q, str)):
            self.q = int(q)
        else:
            self.q = q
        self.tup = (self.m, self.f, self.l, self.o, self.q)
        self.hash = hash(self.tup)

    def __repr__(self):
        return f"ExpConfig({str(self)})"

    def __str__(self):
        return f"m={self.m}, f={self.f}, l={self.l}, o={self.o}, q={self.q}"

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if (not hasattr(other, 'tup')):
            return NotImplemented
        return self.tup == other.tup

    def __lt__(self, other):
        if (not hasattr(other, 'tup')):
            return NotImplemented
        return self.tup < other.tup


class Exp:
    def __init__(self, result: str, formula_val: str, expect_val: str,
                 formula_time: str, expect_time: str, faults: str):
        self.result: bool = True if result == 'Passed' else False
        self.formula_val: float = float(formula_val)
        self.expect_val: float = float(expect_val)
        self.formula_time: timedelta = convert(formula_time)
        self.expect_time: timedelta = convert(expect_time)
        self.faults: Dict[Any, Set[int]] = literal_eval(faults)

    def __repr__(self):
        return f"Exp({str(self)})"

    def __str__(self):
        res = 'Passed' if self.result else 'FAILED'
        return (f"{res} {self.formula_val} = {self.expect_val} "
                f"[{self.formula_time};{self.expect_time}] ({self.faults})")


class Setup(NamedTuple):
    m: List[int]
    f: List[int]
    l: List[int]
    o: List[int]
    q: List[int]

    def __repr__(self):
        return f'Setup({self})'

    def __str__(self):
        return (f'Setup: m={self.m}, f={self.f}, l={self.l}, o={self.o}, '
                f'q={self.q}')

    def __iter__(self):
        return SetupIter(self)


class SetupIter(Iterator):
    def __init__(self, setup: Setup):
        self.iter = product(setup.m, setup.f, setup.l, setup.o, setup.q)

    def __next__(self):
        return ExpConfig(*next(self.iter))


def convert(s: str):
    t = datetime.strptime(s, "%H:%M:%S.%f")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second,
                     microseconds=t.microsecond)


def read_exp_file(file: str) -> Tuple[Dict[ExpConfig, List[Exp]],
                                      Optional[Setup]]:
    exps: Dict[ExpConfig, List[Exp]] = {}
    setup: Optional[Setup] = None
    cur_exp_conf = None
    with open(file) as inp:
        for i, line in enumerate(inp):
            line = line.strip()
            if (line.startswith("Setup")):
                m = re.fullmatch("Setup: m=(.+), f=(.+), l=(.+), o=(.+), "
                                 "q=(.+)", line)
                if (m is None):
                    raise ValueError(f"Could not read in line {i}: \"{line}\"")
                else:
                    args = []
                    for i in range(1, 6):
                        args.append(literal_eval(m.group(i)))
                    setup = Setup(*args)
            elif (line.startswith("m=")):
                m = re.fullmatch("m=([0-9]+), f=([0-9]+), l=([0-9]+), "
                                 "o=([0-9]+), q=([0-9]+)", line)
                if (m is None):
                    raise ValueError(f"Could not read in line {i}: \"{line}\"")
                else:
                    expConf = ExpConfig(m.group(1), m.group(2), m.group(3),
                                        m.group(4), m.group(5))
                    cur_exp_conf = expConf
                    exps[cur_exp_conf] = list()
            else:
                m = re.fullmatch("(Passed|FAILED) ([0-9.]+) = ([0-9.]+) "
                                 "\\[([0-9.:]+);([0-9.:]+)\\] \\(({.+})\\)",
                                 line)
                if (m is None):
                    raise ValueError(f"Could not read in line {i}: \"{line}\"")
                else:
                    exp = Exp(m.group(1), m.group(2), m.group(3), m.group(4),
                              m.group(5), m.group(6))
                    if (cur_exp_conf is None):
                        raise ValueError("No current experiment config to "
                                         f"read in line {i}: \"{line}\"")
                    exps[cur_exp_conf].append(exp)
    return exps, setup


def steimann(tie_size: int, num_faults: int, target: int) -> Fraction:
    return target * Fraction(tie_size-num_faults, num_faults+1)


def combine(exps1: Optional[Dict[ExpConfig, List[Exp]]],
            setup1: Optional[Setup],
            exps2: Optional[Dict[ExpConfig, List[Exp]]],
            setup2: Optional[Setup]) \
            -> Tuple[Optional[Dict[ExpConfig, List[Exp]]], Optional[Setup]]:
    # combine the experiments
    exps_comb = None
    if (exps1 is not None and exps2 is not None):
        exps_comb_d = defaultdict(list)
        for key in sorted(set().union(exps1.keys(), exps2.keys())):
            exps_comb_d[key].extend(exps1.get(key, []))
            exps_comb_d[key].extend(exps2.get(key, []))
        exps_comb = dict(exps_comb_d)
    elif (exps1 is not None):
        exps_comb = exps1
    elif (exps2 is not None):
        exps_comb = exps2
    setup_comb = None
    if (setup1 is not None and setup2 is not None):  # combine the setups
        vals = list()
        for i in range(len(setup1)):
            cur_vals: List[int] = sorted(set().union(setup1[i], setup2[i]))
            vals.append(cur_vals)
        setup_comb = Setup(*vals)
    elif (setup1 is not None):
        setup_comb = setup1
    elif (setup2 is not None):
        setup_comb = setup2
    return exps_comb, setup_comb


if __name__ == "__main__":
    exps, setup = None, None
    for arg in sys.argv[1:]:
        exps, setup = combine(exps, setup, *read_exp_file(arg))

    # print(setup)
    if (exps is not None):
        for exp_config in exps:
            # print(exp_config)
            for exp in exps[exp_config]:
                num_faulty = len(set().union(*exp.faults.values()))
                # print(exp)
                steimann_start = time.time()
                steimann_val = float(steimann(exp_config.m, num_faulty,
                                              exp_config.q))
                steimann_end = time.time()
                s_dur = steimann_end - steimann_start
                steimann_time = timedelta(seconds=s_dur)
                print(exp.expect_time - exp.formula_time,
                      exp.expect_time - steimann_time)
                # print(exp.expect_val, exp.formula_val,
                #       steimann_val, sep='\t')
    # print(exps, setup)
    # points = []
    # while ((line := sys.stdin.readline()) != ""):
    #     formula, expected = (convert(s) for s in line.split())
    #     points.append((expected - formula)/expected)
    # plt.hist(points)
    # plt.show()
