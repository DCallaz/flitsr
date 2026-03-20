from fractions import Fraction
from itertools import permutations, chain, combinations
from math import factorial, ceil, comb
from typing import List, Any, Optional, Set, Dict, Tuple
from flitsr.spectrum import Spectrum
from flitsr.ranking import Rankings, Ranking, Rank
from deprecated.sphinx import deprecated, versionadded


def falling(n, k):
    """
    Calculates the `k`th falling factorial of `n`.
    """
    res = 1
    for i in range(k):
        res *= n
        n -= 1
    return res


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
        if (collapse):
            return len(self._all_fault_groups)
        else:
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

    def old_expected_value(self, q, weffort: bool, collapse=False) -> float:
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

    def expected_value(self, q: int, weffort: bool,
                       collapse=False) -> float:
        """
        Calculates the expected value of the qth fault in this tie. The
        expected value can either be in terms of wasted effort (not
        counting fault inspection) or actual position in the ranking.
        """
        if (self.num_faults() == 1):  # single-fault shortcut
            return self.single_fault_exp_value(q, weffort, collapse)
        elif ((all(len(ls) == 1 for ls in self.active_faults().values()) and
               all(len(fs) == 1 for fs in self.active_fault_locations().values())) or
              (q == 1)):  # single-loc or first fault shortcut
            return self.single_loc_exp_value(q, weffort, collapse)
        else:
            return self.multi_fault_exp_value(q, weffort, collapse)

    def single_fault_exp_value(self, q: int, weffort: bool,
                               collapse=False) -> float:
        print("single fault")
        assert (self.num_faults() == 1)
        l = self.num_active_fault_locs(collapse)
        m = self.len()
        return float(Fraction(m-l, l+1))

    def single_loc_exp_value(self, q: int, weffort: bool,
                             collapse=False) -> float:
        print("single loc")
        l = self.num_active_fault_locs(collapse)
        m = self.len()
        return float(q*Fraction(m-l, l+1))

    def multi_fault_exp_value(self, q: int, weffort: bool, collapse=False):
        print("multi fault")
        l = self.num_active_fault_locs(collapse)
        k = min(q, self.num_faults())
        m = self.len()
        res = 0.0
        F = self.active_faults(collapse)
        f = self.num_faults()
        print(F)
        for i in range(1, l+1):  # iterate over each fault loc
            exp_val = Fraction(i*m, l+1)
            for n in range(1, k+1):  # iterate over number of faults found
                for K in combinations(F, n):
                    all_f = set.union(*[F[fn] for fn in K])
                    perms = ((-1)**(k - len(K)) * comb(f-len(K), k-len(K)) *
                             Fraction(falling(len(all_f), i), falling(l, i)))
                    print(K, all_f, exp_val, perms)
                    res += exp_val * perms
        return float(res)

    def _add_entity(self, entity: Spectrum.Entity,
                    active_faults: Dict[Any, Set[Spectrum.Element]],
                    inactive_faults: Dict[Any, Set[Spectrum.Element]]):
        self._elems.update(entity)
        self._group_len += 1

        if (len(active_faults) > 0 or len(inactive_faults) > 0):
            self._num_fault_groups += 1

        seen_fault_locs: Set[Spectrum.Element] = set()
        for (fault_num, fault_locs) in active_faults.items():
            # set number of faults
            if (fault_num not in self._fault_locs):
                self._num_faults += 1
            # set faulty groups
            self._fault_groups.setdefault(fault_num, set()).add(entity[0])
            self._all_fault_groups.setdefault(entity[0], set()).add(fault_num)
            # set faulty elements
            self._fault_locs.setdefault(fault_num, set()).update(fault_locs)
            for fault_loc in fault_locs:
                if (fault_loc not in seen_fault_locs):
                    self._num_fault_locs += 1
                    seen_fault_locs.add(fault_loc)
                self._all_fault_locs.setdefault(fault_loc,
                                                set()).add(fault_num)

        # update numbers for inactive faults
        inactive_locs = set().union(*inactive_faults.values())
        self._num_fault_locs += len(inactive_locs.difference(seen_fault_locs))

    def __str__(self):
        return str(self._elems)


class Ties:
    class _RankingIter:
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

    @staticmethod
    def _get_tie_entities(ri: _RankingIter) -> Set[Spectrum.Entity]:
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

    @staticmethod
    def _get_faults(entity: Spectrum.Entity,
                    faults: Dict[Any, Set[Spectrum.Element]],
                    seen_faults: Set[Any]) -> Tuple[
                    Dict[Any, Set[Spectrum.Element]],
                    Dict[Any, Set[Spectrum.Element]]]:
        """
        Return all identified faults found in the given entity, both active and
        inactive.

        Args:
          entity: The Entity to check for faults in.
          faults: A dictionary of all the faults in the subject system, with
            keys being the fault IDs, and values being the set of fault
            locations.
          seen_faults: A set of all the faults that have already been
            identified in a previous tie.

        Returns:
          A Tuple of the active and inactive faults (in that order) identified
          in the given entity. The format is the same as for the `faults`
          parameter given as input.
        """
        active_faults: Dict[Any, Set[Spectrum.Element]] = {}
        inactive_faults: Dict[Any, Set[Spectrum.Element]] = {}
        for (fault_num, fault_locs) in faults.items():
            cur_fault_locs = set(fault_locs).intersection(entity)
            if (len(cur_fault_locs) == 0):    # no locs in this entity: skip
                continue
            elif (fault_num in seen_faults):  # already seen: inactive fault
                inactive_faults.setdefault(fault_num,
                                           set()).update(cur_fault_locs)
            else:                             # not seen before: active fault
                active_faults.setdefault(fault_num,
                                         set()).update(cur_fault_locs)
        return active_faults, inactive_faults

    def __init__(self, rankings: Rankings):
        self.faults = rankings.faults()
        seen_faults: Set[Any] = set()
        seen_entities: Set[Spectrum.Entity] = set()
        self.ties: List[Tie] = []
        # Populate this Ties object
        r_iters = [self._RankingIter(r) for r in rankings]
        while (any(ri.is_active() for ri in r_iters)):
            # Get all entities with the same score
            all_entities: Set[Spectrum.Entity] = set()
            for ri in r_iters:
                if (ri.is_active()):
                    entities = self._get_tie_entities(ri)
                    all_entities.update(entities)
            # Form the tie
            tie = Tie()
            cur_faults: Set[Any] = set()  # faults identified in this tie
            for entity in all_entities.difference(seen_entities):
                a_fault, ia_fault = self._get_faults(entity, self.faults,
                                                     seen_faults)
                tie._add_entity(entity, a_fault, ia_fault)
                cur_faults.update(a_fault.keys())
            seen_faults.update(cur_faults)
            seen_entities.update(all_entities)
            self.ties.append(tie)
        # Add elements not seen to bottom of tie
        not_seen: Set[Spectrum.Element] = set(rankings.elements())
        for entity in seen_entities:
            not_seen.difference_update(entity)
        tie = Tie()
        cur_faults = set()
        for entity in not_seen:
            a_fault, ia_fault = self._get_faults(entity, self.faults,
                                                 seen_faults)
            tie._add_entity(entity, a_fault, ia_fault)
            cur_faults.update(a_fault.keys())
        seen_faults.update(cur_faults)
        self.ties.append(tie)
        self._num_entities = len(seen_entities)
        self._num_elems = len(rankings.elements())

    def __iter__(self):
        return iter(self.ties)

    def __getitem__(self, index: int):
        return self.ties[index]

    def __len__(self):
        return len(self.ties)

    def size(self, collapse=False):
        if (collapse):
            return self._num_entities
        else:
            return self._num_elems
