import copy
from fractions import Fraction
from itertools import permutations, chain
from math import factorial, ceil
from typing import List, Any, Optional, Set, Dict
from flitsr.spectrum import Spectrum
from flitsr.ranking import Rankings, Ranking, Rank
from deprecated.sphinx import deprecated, versionadded


class Tie:
    def __init__(self):
        self._elems: Set[Spectrum.Element] = set()
        self._group_len = 0
        self._fault_locs: Dict[Any, Set[Spectrum.Element]] = {}
        self._fault_groups: Dict[Any, Set[Spectrum.Element]] = {}
        self._num_faults = 0
        self._num_fault_locs = 0
        self._num_fault_groups = 0
        self._all_fault_locs: Dict[Spectrum.Element, Set[Any]] = {}
        self._all_fault_groups: Dict[Spectrum.Element, Set[Any]] = {}

    def len(self, collapse=False) -> int:
        """
        Return either the number of groups (if collapsed), or number of
        elements in this tie (if not collapsed).
        """
        if (collapse):
            return self._group_len
        else:
            return len(self._elems)

    def elems(self) -> Set[Spectrum.Element]:
        """Return the set of all the elements in this tie"""
        return self._elems

    @versionadded(version='2.4.0')
    def active_faults(self, collapse=False) \
            -> Dict[Any, Set[Spectrum.Element]]:
        """
        Return a dictionary of all faults seen for the fime time in this tie,
        along with their fault locations (either groups or elements). This is a
        subset of the ``Ties.faults`` dictionary.
        """
        if (collapse):
            return self._fault_groups
        else:
            return self._fault_locs

    def num_faults(self) -> int:
        """
        Return the number of unique faults found for the first time in this
        tie.
        """
        return self._num_faults

    def num_fault_locs(self, collapse=False) -> int:
        """
        Return the total number of faulty locations (either groups or elements)
        in this tie. NOTE: this includes both active and non-active fault
        locations. Active fault locations are those of faults seen for the
        first time in this tie, while non-active are those of faults already
        seen in a previous tie.
        """
        if (collapse):
            return self._num_fault_groups
        else:
            return self._num_fault_locs

    def num_active_fault_locs(self, collapse=False) -> int:
        """
        Return only the number of active fault locations (either groups or
        elements) in this tie. An active fault location is a fault location
        that belongs to a fault that is seen for the first time in this tie.
        """
        return len(self._all_fault_locs)

    @deprecated(version='2.4.0', reason='This function has been renamed to '
                '`Tie.active_fault_locations`.')
    def fault_groups(self, collapse=False) -> Dict[Spectrum.Element, Set[Any]]:
        """
        Return all active fault locations (either groups or elements) in
        this tie, with the faults they contain. Active fault locations are
        those of faults seen for the first time in this tie.
        """
        return self.active_fault_locations(collapse=collapse)

    @versionadded(version='2.4.0', reason='Renamed from `Tie.fault_groups`.')
    def active_fault_locations(self, collapse=False) \
            -> Dict[Spectrum.Element, Set[Any]]:
        """
        Return all active fault locations (either groups or elements) in
        this tie, with the faults they contain. Active fault locations are
        those of faults seen for the first time in this tie.
        """
        if (collapse):
            return self._all_fault_groups
        else:
            return self._all_fault_locs

    def expected_value(self, q, weffort: bool, collapse=False) -> float:
        """
        Calculates the expected value of the qth fault in this tie. The
        expected value can either be in terms of wasted effort (not
        counting fault inspection) or actual position in the ranking.
        """
        fs = self.fault_groups(collapse)
        dups = sorted(chain(*fs.values()))
        m = self.len(collapse)
        l = self.num_fault_locs(collapse)
        l_a = self.num_active_fault_locs(collapse)
        nf = self.num_faults()
        if (weffort):
            expval = Fraction(m-l, l_a+1)
        else:
            expval = Fraction(m+1, l_a+1)
        # first fault or all 1 fault per loc
        if (q == 1 or (l_a == nf and all(len(ls) == 1 for ls in fs.values()))):
            return float(q*expval)
        elif (l_a > 10 or len(dups) == len(set(dups))):  # approx. solution or all single loc
            fpl = Fraction(nf, l_a)  # faults per (active) location
            for i in range(1, l_a+1):
                if (ceil(fpl*i) >= q):
                    if (fpl*i >= q):  # exactly contained in location
                        return float(expval*i)
                    else:  # contained between this location and the next
                        return float(expval*(i + (1 - ((fpl*i) % 1))))
            raise ValueError(f"Could not find fault {q}")
        else:
            dist = {}
            for rank in permutations(fs.keys()):
                seen = set()
                tot = 0
                for elem in rank:
                    tot += 1
                    seen.update(fs[elem])
                    if (len(seen) >= q):
                        break
                if (tot not in dist):
                    dist[tot] = 0
                dist[tot] += 1
            frac = Fraction(sum(v*c for v, c in dist.items()), factorial(l_a))
            return float(expval*frac)

    def _add_entity(self, entity: Spectrum.Entity,
                    faults: Dict[Any, Set[Spectrum.Element]],
                    seen_faults: Set[Any]):
        self._elems.update(entity)
        self._group_len += 1
        # Check if fault is in group
        faulty_group = False
        seen_fault_locs: Set[Spectrum.Element] = set()
        for (fault_num, fault_locs) in faults.items():
            unseen_fault = False
            for fault_loc in set(fault_locs).intersection(entity):
                # Check & update fault number
                if (fault_num not in seen_faults):
                    unseen_fault = True
                    self._num_faults += 1
                    seen_faults.add(fault_num)
                # Check & update faulty locs
                if (fault_loc not in seen_fault_locs):
                    seen_fault_locs.add(fault_loc)
                    self._num_fault_locs += 1
                    if (unseen_fault):
                        self._all_fault_locs.setdefault(fault_loc,
                                                        set()).add(fault_num)
                        self._fault_locs.setdefault(fault_num,
                                                    set()).add(fault_loc)
                # Check & update faulty group
                if (not faulty_group):
                    self._num_fault_groups += 1
                    faulty_group = True
                    if (unseen_fault):
                        self._all_fault_groups.setdefault(entity[0],
                                                          set()).add(fault_num)
                        self._fault_groups.setdefault(fault_num,
                                                      set()).add(entity[0])


class Ties:
    def __init__(self, rankings: Rankings):
        self.faults = rankings.faults()
        seen_faults: Set[Any] = set()
        seen_entities: Set[Spectrum.Entity] = set()
        self.ties: List[Tie] = []
        class RankingIter:
            def __init__(self, ranking: Ranking):
                self.r_iter = iter(ranking)
                self.cur: Optional[Rank] = next(self.r_iter, None)
            def is_active(self) -> bool:
                return self.cur is not None
            def consume(self) -> Rank:
                if (self.cur is None):
                    raise StopIteration("No more elements in ScoreIter")
                old_cur = self.cur
                self.cur = next(self.r_iter, None)
                return old_cur
            def cur_score(self):
                if (self.cur is not None):
                    return self.cur.score
                else:
                    raise StopIteration()
        r_iters = [RankingIter(r) for r in rankings]
        # Populate this Ties object
        def get_tie_entities(ri: RankingIter) -> Set[Spectrum.Entity]:
            entities: Set[Spectrum.Entity] = set()
            # sanity check
            if (not ri.is_active()):
                return entities
            # Get all UUTs with same score
            score = ri.cur_score()
            while (ri.is_active() and ri.cur_score() == score):
                r = ri.consume()
                entities.add(r.entity)
            return entities
        while (any(ri.is_active() for ri in r_iters)):
            all_entities: Set[Spectrum.Entity] = set()
            for ri in r_iters:
                if (ri.is_active()):
                    entities = get_tie_entities(ri)
                    all_entities.update(entities)
            tie = Tie()
            for entity in all_entities.difference(seen_entities):
                tie._add_entity(entity, self.faults, seen_faults)
            seen_entities.update(all_entities)
            self.ties.append(tie)
        # Add elements not seen to bottom of tie
        not_seen: Set[Spectrum.Element] = set(rankings.elements())
        for entity in seen_entities:
            not_seen.difference_update(entity)
        tie = Tie()
        for entity in not_seen:
            tie._add_entity(entity, self.faults, seen_faults)
        self.ties.append(tie)
        self._num_entities = len(seen_entities)
        self._num_elems = len(rankings.elements())

    def __iter__(self):
        return iter(self.ties)

    def size(self, collapse=False):
        if (collapse):
            return self._num_entities
        else:
            return self._num_elems
