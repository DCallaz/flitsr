from fractions import Fraction
from itertools import permutations, chain
from collections import defaultdict
from math import factorial, ceil
from typing import List, Any, Optional, Set, Dict, Tuple, Iterable, \
        Collection, NamedTuple, Union, overload, Literal
from flitsr.spectrum import Spectrum
from flitsr.ranking import Rankings, Ranking, Rank
from flitsr.calculations.bu_model import BUModel
from deprecated.sphinx import deprecated, versionadded, versionchanged
AnyEntitiesDict = Union[Dict[Any, Set[Spectrum.Element]],
                        Dict[Any, Set[Spectrum.Entity]]]
RevAnyEntitiesDict = Union[Dict[Spectrum.Element, Any],
                           Dict[Spectrum.Entity, Any]]
AnyEntities = Union[Set[Spectrum.Element], Set[Spectrum.Entity]]


class _CollapsableFault(NamedTuple):
    locs: Set[Spectrum.Element]
    groups: Set[Spectrum.Entity]


class Tie:
    def __init__(self, entities: Collection[Spectrum.Entity], all_faults:
                 Dict[Any, _CollapsableFault],
                 active_faults: Dict[Any, int]):
        self._group_len = len(entities)
        self._active_faults = active_faults
        self._fault_locs: Dict[Any, Set[Spectrum.Element]] = {}
        self._fault_groups: Dict[Any, Set[Spectrum.Entity]] = {}
        self._elems: Set[Spectrum.Element] = set()
        for entity in entities:
            self._elems.update(entity)
        # copy over the faults & fault groups
        for (fault_num, fault_locs) in all_faults.items():
            # set faulty groups
            self._fault_groups[fault_num] = fault_locs.groups
            # set faulty elements
            self._fault_locs[fault_num] = fault_locs.locs

    def set_active(self, active: Dict[Any, int]):
        """
        (Re-)set the active faults in this tie to be the ones given.

        Args:
          active: A dictionary of each of the active faults with the number of
            locations in this tie that are necessary to identify them.
        """
        self._active_faults = active

    def len(self, collapse=False) -> int:
        """
        Return either the number of groups (if collapsed), or number of
        elements in this tie (if not collapsed).
        """
        if (collapse):
            return self._group_len
        else:
            return len(self._elems)

    @overload
    def elems(self) -> Set[Spectrum.Element]: ...

    @overload
    def elems(self, collapse: Literal[False]) -> Set[Spectrum.Element]: ...

    @overload
    def elems(self, collapse: Literal[True]) -> Set[Spectrum.Entity]: ...

    @versionchanged(version='2.5.0', reason='Added the `collapse` optional '
                    'parameter')
    def elems(self, collapse=False) -> AnyEntities:
        """Return the set of all the elements (or entities) in this tie"""
        return self._elems

    @staticmethod
    def _get_fault_locs(fault_dict: AnyEntitiesDict,
                        faults: Iterable) -> AnyEntities:
        return set().union(*(fault_dict[k] for k in faults))

    @overload
    def active_faults(self) -> Dict[Any, Set[Spectrum.Element]]: ...

    @overload
    def active_faults(self, collapse: Literal[False]) \
        -> Dict[Any, Set[Spectrum.Element]]: ...

    @overload
    def active_faults(self, collapse: Literal[True]) \
        -> Dict[Any, Set[Spectrum.Entity]]: ...

    @versionadded(version='2.4.0')
    def active_faults(self, collapse=False) \
            -> AnyEntitiesDict:
        """
        Return a dictionary of all faults identified in this tie, along with
        their fault locations (either groups or elements). This is a subset of
        the ``Ties.faults`` dictionary.
        """
        if (collapse):
            return {k: self._fault_groups[k] for k in self._active_faults}
        else:
            return {k: self._fault_locs[k] for k in self._active_faults}

    @versionchanged(version='2.5.0', reason='Added the `active` optional '
                    'parameter')
    def num_faults(self, active=True) -> int:
        """
        Return the number of faults in this tie. Either returns only the number
        of active faults (default), or the total number of faults if `active`
        is False.
        """
        if (active):
            return len(self._active_faults)
        else:
            return len(self._fault_locs)

    @versionchanged(version='2.5.0', reason='Added the `active` optional '
                    'parameter')
    def num_fault_locs(self, collapse=False, active=False) -> int:
        """
        Return the total number of faulty locations (either groups or elements)
        in this tie. By default, returns the locations of both active and
        passive faults. If `active` is True, returns only the locations of
        active faults. Active fault locations are those of faults conclusively
        identified in this tie, while non-active are those of faults identified
        in a previous or subsequent tie.
        """
        # first get all the faults to include (active or all)
        faults: Iterable
        if (active):
            faults = self._active_faults.keys()
        else:
            faults = self._fault_locs.keys()
        # construct the set of locations and find its length
        if (collapse):
            return len(self._get_fault_locs(self._fault_groups, faults))
        else:
            return len(self._get_fault_locs(self._fault_locs, faults))

    def num_active_fault_locs(self, collapse=False) -> int:
        """
        Return only the number of active fault locations (either groups or
        elements) in this tie. An active fault location is a fault location
        that belongs to a fault that is identified in this tie. This method is
        equivalent to `num_fault_locs(active=True)<Tie.num_fault_locs>`.
        """
        return self.num_fault_locs(collapse=collapse, active=True)

    @overload
    def fault_groups(self) -> Dict[Spectrum.Element, Any]: ...

    @overload
    def fault_groups(self, collapse: Literal[False]) \
        -> Dict[Spectrum.Element, Any]: ...

    @overload
    def fault_groups(self, collapse: Literal[True]) \
        -> Dict[Spectrum.Entity, Any]: ...

    @deprecated(version='2.4.0', reason='This function has been renamed to '
                '`Tie.active_fault_locations`.')
    def fault_groups(self, collapse=False) -> RevAnyEntitiesDict:
        """
        Return all active fault locations (either groups or elements) in
        this tie, with the faults they contain. Active fault locations are
        those of faults identified in this tie.
        """
        return self.active_fault_locations(collapse=collapse)

    @overload
    def active_fault_locations(self) -> Dict[Spectrum.Element, Any]: ...

    @overload
    def active_fault_locations(self, collapse: Literal[False]) \
        -> Dict[Spectrum.Element, Any]: ...

    @overload
    def active_fault_locations(self, collapse: Literal[True]) \
        -> Dict[Spectrum.Entity, Any]: ...

    @versionadded(version='2.4.0', reason='Renamed from `Tie.fault_groups`.')
    def active_fault_locations(self, collapse=False) -> RevAnyEntitiesDict:
        """
        Return all active fault locations (either groups or elements) in
        this tie, with the faults they contain. Active fault locations are
        those of faults identified in this tie.
        """
        fault_dict = self._fault_groups if collapse else self._fault_locs
        ret_dict = defaultdict(set)
        for fault in self._active_faults:
            for loc in fault_dict[fault]:
                ret_dict[loc].add(fault)
        return dict(ret_dict)

    @versionadded(version='2.5.0', reason='Added support for multiple bug '
                  'understanding models')
    def fault_identify_nums(self, collapse=False) -> Dict[Any, int]:
        """
        Return a dictionary with the number of locations that must be inspected
        (according to the bug understanding model) to identify each of the
        active faults in this tie.

        Returns:
          A dictionary with keys being each of the active faults, and values
          being the number of locations of that fault in this tie that must
          be inspected to conclusively identify the fault.
        """
        if (collapse is False):
            return self._active_faults.copy()
        else:
            active_fault_group_nums: Dict[Any, int] = dict()
            for fault in self._active_faults:
                num_groups = self._get_identify_group_num(fault)
                # add this num to dict
                active_fault_group_nums[fault] = num_groups
            return active_fault_group_nums

    @versionadded(version='2.5.0', reason='Added support for multiple bug '
                  'understanding models')
    def fault_identify_num(self, fault: Any, collapse=False) -> int:
        """
        Return the number of locations that must be inspected (according to the
        bug understanding model) to identify the given fault in this tie.

        Raises:
          ValueError: If `fault` is not an active fault in this tie.
        """
        try:
            if (collapse is False):
                return self._active_faults[fault]
            else:
                return self._get_identify_group_num(fault)
        except KeyError as e:
            raise ValueError(f"{fault} is not an active fault in this tie!") \
                    from e

    def _get_identify_group_num(self, fault: Any) -> int:
        """Get the number of groups necessary to identify the given fault"""
        num_locs = self._active_faults[fault]
        # calculate the estimated num groups to be inspected
        loc_ratio = Fraction(num_locs, self.num_faults())
        num_fault_groups = self.num_active_fault_locs(True)
        num_groups = ceil(loc_ratio * num_fault_groups)
        return num_groups

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
    def _get_faults(entities: Iterable[Spectrum.Entity],
                    faults: Dict[Any, Set[Spectrum.Element]],
                    to_inspect: Dict[Any, int]) -> Tuple[
                    Dict[Any, _CollapsableFault],
                    Dict[Any, int]]:
        """
        Return all identified faults found in the given iterable of entities,
        as well as a set of the faults that are active.

        Args:
          entities: An iterable of entities to check for faults in.
          faults: A dictionary of all the faults in the subject system, with
            keys being the fault IDs, and values being the set of fault
            locations.
          to_inspect: A dictionary with the number of fault locations that
            still need to be inspected to identify each fault.

        Returns:
          A Tuple with the first entry being a dictionary with all the faults
          identified in the given entities, along with the set of locations and
          groups for them in this tie, and the second a dictionary of
          all active faults and the number of locations needed to identify
          them.
        """
        def dflt(): return _CollapsableFault(set(), set())
        all_faults: Dict[Any, _CollapsableFault] = defaultdict(dflt)
        active_faults: Dict[Any, int] = {}
        for (fault_num, fault_locs) in faults.items():
            cur_fault_locs: Set[Spectrum.Element] = set()
            cur_fault_groups: Set[Spectrum.Entity] = set()
            for entity in entities:
                cur = fault_locs.intersection(entity)
                cur_fault_locs.update(cur)
                # get cur fault groups
                if (len(cur) > 0):
                    cur_fault_groups.add(entity)
            if (len(cur_fault_locs) == 0):    # no locs in this entity: skip
                continue
            all_faults[fault_num].locs.update(cur_fault_locs)
            all_faults[fault_num].groups.update(cur_fault_groups)
            # check if active: if we find this fault in this set of entities
            if (len(cur_fault_locs) >= to_inspect[fault_num] and
                    to_inspect[fault_num] > 0):
                active_faults[fault_num] = to_inspect[fault_num]
        return dict(all_faults), active_faults

    def __init__(self, rankings: Rankings, bu: BUModel):
        """
        Construct the ties for the given set of rankings and bug understanding
        model.

        Args:
          rankings: The set of rankings to construct the ties for.
          bu: The bug understanding model; a dictionary with each fault and the
            associated number of locations to inspect for identifying that
            fault.
        """
        self.faults = rankings.faults()
        self.bu_model = bu
        to_inspect: Dict[Any, int] = bu.get_dict(self.faults)
        # set keeping track of seen entities - no repetitions
        seen_entities: Set[Spectrum.Entity] = set()
        self.ties: List[Tie] = []
        # Populate this Ties object
        r_iters = [self._RankingIter(r) for r in rankings]
        while (any(ri.is_active() for ri in r_iters)):
            # Get all entities with the same score
            entities: Set[Spectrum.Entity] = set()
            for ri in r_iters:
                if (ri.is_active()):
                    entities.update(self._get_tie_entities(ri))
            # Form the tie
            fs, active = self._get_faults(entities, self.faults, to_inspect)
            tie = Tie(entities, fs, active)
            # update counters
            for fault in fs:
                to_inspect[fault] -= len(fs[fault].locs)
            seen_entities.update(entities)
            self.ties.append(tie)
        # Add elements not seen to bottom of tie
        not_seen: Set[Spectrum.Element] = set(rankings.elements())
        for entity in seen_entities:
            not_seen.difference_update(entity)
        # Form the tie
        fs, active = self._get_faults(not_seen, self.faults, to_inspect)
        tie = Tie(not_seen, fs, active)
        # update counters
        for fault in fs:
            to_inspect[fault] -= len(fs[fault])
        self.ties.append(tie)
        self._num_entities = len(seen_entities)
        self._num_elems = len(rankings.elements())

    def set_bug_understanding(self, bu: BUModel):
        """
        Changes the bug understanding model to be the one given by `bu`. This
        updates each of the contained `Tie`'s active and passive faults to
        reflect when (i.e., in which `Tie`) each fault would be localized.
        """
        to_inspect: Dict[Any, int] = bu.get_dict(self.faults)
        for tie in self:
            active: Dict[Any, int] = {}
            for fault, fault_locs in self.faults.items():
                if (len(tie._fault_locs.get(fault, [])) >= to_inspect[fault]
                        and to_inspect[fault] > 0):
                    active[fault] = to_inspect[fault]
                to_inspect[fault] -= len(tie._fault_locs.get(fault, []))
            tie.set_active(active)

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
