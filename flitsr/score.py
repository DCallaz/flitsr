import random
from typing import Callable, List, Any, Optional, Set, Dict
from flitsr.spectrum import Spectrum
import copy


class Scores:
    class Score:
        """
        A element from a spectrum, together with its scores.
        """
        def __init__(self, elem: Spectrum.Element, score: float,
                     exec_count: int):
            self.elem = elem
            self.score = score
            self.exec = exec_count

        def __str__(self):
            return "(" + str(self.elem) + ", " + str(self.score) + ")"

        def __repr__(self):
            return str(self)

    def __init__(self):
        self._scores: List[Scores.Score] = []
        self.elem_map: Dict[Spectrum.Element, Scores.Score] = {}
        self.place = 0

    def __getitem__(self, elem):
        return self.elem_map[elem]

    def sort(self, reverse: bool, tiebrk: int):
        if (tiebrk == 1):  # Sorted by execution counts
            self._scores.sort(key=lambda x: x.exec, reverse=reverse)
            self._scores.sort(key=lambda x: x.score, reverse=reverse)
        elif (tiebrk == 2):  # random ordering
            random.shuffle(self._scores)
            self._scores.sort(key=lambda x: x.score, reverse=reverse)
        elif (tiebrk == 3):  # original ranking tie break
            if (orig is not None):  # sort by original rank then exec count
                self._scores.sort(key=lambda x: orig[x.elem].exec,
                                  reverse=reverse)
                self._scores.sort(key=lambda x: orig[x.elem].score,
                                  reverse=reverse)
            else:  # if no orig, still sort by current execution count
                self._scores.sort(key=lambda x: x.exec, reverse=reverse)
            self._scores.sort(key=lambda x: x.score, reverse=reverse)
        else:
            self._scores.sort(key=lambda x: x.score, reverse=reverse)

    def append(self, elem: Spectrum.Element, score: float, exec_count: int):
        created = Scores.Score(elem, score, exec_count)
        self._scores.append(created)
        self.elem_map[elem] = created

    def extend(self, scores: List[Score]):
        self._scores.extend(scores)
        for score in scores:
            self.elem_map[score.elem] = score

    def __iter__(self):
        return iter(self._scores)

    def __len__(self):
        return len(self._scores)


class Ties:
    class Tie:
        def __init__(self):
            self._elems: Set[Spectrum.Element] = set()
            self._group_len = 0
            self._num_faults = 0
            self._fault_locs = 0
            self._fault_groups = 0

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
                    # Check & update faulty group
                    if (not faulty_group):
                        self._fault_groups += 1
                        faulty_group = True

    def __init__(self, spectrum: Spectrum, scores: List[Scores]):
        self.faults: Dict[int, List[Spectrum.Element]] = spectrum.get_faults()
        # needed to remove groups of fault locations
        faults = copy.deepcopy(self.faults)
        seen_faults: Set[int] = set()
        seen_elements: Set[Spectrum.Element] = set()
        self.ties: List[Ties.Tie] = []
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
            tie = Ties.Tie()
            for elem in all_elems.difference(seen_elements):
                group = spectrum.get_group(elem)
                tie._add_group(group, faults, seen_faults)
            seen_elements.update(all_elems)
            self.ties.append(tie)
        # Add elements not seen to bottom of tie
        not_seen = [e for e in spectrum.elements() if e not in seen_elements]
        tie = Ties.Tie()
        for elem in not_seen:
            group = spectrum.get_group(elem)
            tie._add_group(group, faults, seen_faults)
        self.ties.append(tie)

    def __iter__(self):
        return iter(self.ties)


orig: Optional[Scores] = None


def set_orig(scores: Scores):
    global orig
    orig = copy.deepcopy(scores)


def unset_orig():
    global orig
    orig = None
