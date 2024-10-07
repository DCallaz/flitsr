import copy
from fractions import Fraction
from itertools import permutations, chain
from math import factorial, ceil
from typing import List, Any, Optional, Set, Dict
from flitsr.spectrum import Spectrum
from flitsr.score import Scores

class Tie:
    def __init__(self):
        self._elems: Set[Spectrum.Element] = set()
        self._group_len = 0
        self._num_faults = 0
        self._fault_locs = 0
        self._fault_groups = 0
        self._all_fault_locs = {}
        self._all_fault_groups = {}

    def len(self, collapse=False):
        """
        Return either the number of groups (if collapsed), or number of elements
        in this tie (if not collapsed).
        """
        if (collapse):
            return self._group_len
        else:
            return len(self._elems)

    def elems(self):
        """Return the set of all the elements in this tie"""
        return self._elems

    def num_faults(self):
        """
        Return the number of unique faults found for the first time in this
        tie
        """
        return self._num_faults

    def num_fault_locs(self, collapse=False):
        """
        Return the number of faulty locations (either groups or elements) in
        this tie.
        """
        if (collapse):
            return self._fault_groups
        else:
            return self._fault_locs

    def fault_groups(self, collapse=False):
        """
        Return all fault locations (either groups or elements) in
        this tie, with the faults they contain.
        """
        if (collapse):
            return self._all_fault_groups
        else:
            return self._all_fault_locs


    def expected_value(self, q, weffort: bool, collapse=False):
        """
        Calculates the expected value of the qth fault in this tie. The
        expected value can either be in terms of wasted effort (not
        counting fault inspection) or actual position in the ranking.
        """
        fs = self.fault_groups(collapse)
        dups = sorted(chain(*fs.values()))
        m = self.len(collapse)
        l = self.num_fault_locs(collapse)
        nf = self.num_faults()
        if (weffort):
            expval = Fraction(m-l, l+1)
        else:
            expval = Fraction(m+1, l+1)
        # first fault or all 1 fault per loc
        if (q == 1 or (l == nf and all(len(ls) == 1 for ls in fs))):
            return float(q*expval)
        elif (l > 10 or len(dups) == len(set(dups))):  # approx. solution or all single loc
            fpl = Fraction(nf, l)  # faults per location
            for i in range(1, l+1):
                if (ceil(fpl*i) >= q):
                    if (fpl*i >= q):  # exactly contained in location
                        return expval*i
                    else:  # contained between this location and the next
                        return float(expval*(i + (fpl*i % 1)))
        else:
            dist = {}
            for rank in permutations(fs.keys()):
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
            frac = Fraction(sum(v*c for v, c in dist.items()), factorial(l))
            return float(expval*frac)


    def _add_group(self, group: List[Spectrum.Element],
                   faults: Dict[int, List[Spectrum.Element]],
                   seen_faults: Set[int]):
        self._elems.update(group)
        self._group_len += 1
        # Check if fault is in group
        faulty_group = False
        seen_fault_locs: Set[Spectrum.Element] = set()
        for (fault_num, fault_locs) in faults.items():
            for fault_loc in set(fault_locs).intersection(group):
                # Check & update fault number
                if (fault_num not in seen_faults):
                    self._num_faults += 1
                    seen_faults.add(fault_num)
                # Check & update faulty locs
                if (fault_loc not in seen_fault_locs):
                    seen_fault_locs.add(fault_loc)
                    self._fault_locs += 1
                    self._all_fault_locs.setdefault(fault_loc,
                                                    set()).add(fault_num)
                # Check & update faulty group
                if (not faulty_group):
                    self._fault_groups += 1
                    faulty_group = True
                    self._all_fault_groups.setdefault(group[0],
                                                      set()).add(fault_num)


class Ties:
    def __init__(self, spectrum: Spectrum, scores: List[Scores]):
        self.faults: Dict[int, List[Spectrum.Element]] = spectrum.get_faults()
        # needed to remove groups of fault locations
        faults = copy.deepcopy(self.faults)
        seen_faults: Set[int] = set()
        seen_elements: Set[Spectrum.Element] = set()
        self.ties: List[Tie] = []
        class ScoreIter:
            def __init__(self, score):
                self.s_iter = iter(score)
                self.cur = next(self.s_iter, None)
            def is_active(self):
                return self.cur != None
            def consume(self):
                old_cur = self.cur
                self.cur = next(self.s_iter, None)
                return old_cur
            def cur_score(self):
                if (self.cur is not None):
                    return self.cur.score
                else:
                    raise StopIteration()
        s_iters = [ScoreIter(s) for s in scores]
        # Populate this Ties object
        def get_tie_elems(si: ScoreIter) -> Set[Spectrum.Element]:
            elems: Set[Spectrum.Element] = set()
            # sanity check
            if (not si.is_active()):
                return elems
            # Get all UUTs with same score
            score = si.cur_score()
            while (si.is_active() and si.cur_score() == score):
                s = si.consume()
                elems.add(s.elem)
            return elems
        while (any(si.is_active() for si in s_iters)):
            all_elems: Set[Spectrum.Element] = set()
            for si in s_iters:
                if (si.is_active()):
                    elems = get_tie_elems(si)
                    all_elems.update(elems)
            tie = Tie()
            for elem in all_elems.difference(seen_elements):
                group = spectrum.get_group(elem)
                tie._add_group(group, faults, seen_faults)
            seen_elements.update(all_elems)
            self.ties.append(tie)
        # Add elements not seen to bottom of tie
        not_seen = [e for e in spectrum.elements() if e not in seen_elements]
        tie = Tie()
        for elem in not_seen:
            group = spectrum.get_group(elem)
            tie._add_group(group, faults, seen_faults)
        self.ties.append(tie)

    def __iter__(self):
        return iter(self.ties)