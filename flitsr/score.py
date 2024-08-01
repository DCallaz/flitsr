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
        self.scores: List[Scores.Score] = []
        self.place = 0

    def __getitem__(self, elem):
        for score in self.scores:
            if (score.elem == elem):
                return score

    def sort(self, reverse: bool, tiebrk: int):
        if (tiebrk == 1):  # Sorted by execution counts
            self.scores.sort(key=lambda x: x.exec, reverse=reverse)
            self.scores.sort(key=lambda x: x.score, reverse=reverse)
        elif (tiebrk == 2):  # random ordering
            random.shuffle(self.scores)
            self.scores.sort(key=lambda x: x.score, reverse=reverse)
        elif (tiebrk == 3):  # original ranking tie break
            if (orig is not None):  # sort by original rank then exec count
                self.scores.sort(key=lambda x: orig[x.elem].exec,
                                 reverse=reverse)
                self.scores.sort(key=lambda x: orig[x.elem].score,
                                 reverse=reverse)
            else:  # if no orig, still sort by current execution count
                self.scores.sort(key=lambda x: x.exec, reverse=reverse)
            self.scores.sort(key=lambda x: x.score, reverse=reverse)
        else:
            self.scores.sort(key=lambda x: x.score, reverse=reverse)

    def append(self, elem: Spectrum.Element, score: float, exec_count: int):
        created = Scores.Score(elem, score, exec_count)
        self.scores.append(created)

    def get_ties(self, spectrum: Spectrum, worst_effort: bool):
        return Ties(spectrum, self, worst_effort)

    def __iter__(self):
        return iter(self.scores)

    def __len__(self):
        return len(self.scores)


class Ties:
    class Tie:
        def __init__(self, faults: Dict[int, List[Spectrum.Element]],
                     worst_effort: bool):
            self.elems: Set[Spectrum.Element] = set()
            self.group_len = 0
            self.num_faults = 0
            self.fault_locs = 0
            self.fault_groups = 0
            self._faults = faults
            self._worst_effort = worst_effort

        def add_group(self, group: List[Spectrum.Element]):
            self.elems.update(group)
            self.group_len += 1
            # Check if fault is in group
            faulty_group = False
            toRemove = set()
            seen_fault_locs: Set[Spectrum.Element] = set()
            for (fault_num, fault_locs) in self._faults.items():
                worst_toRemove = []
                for fault_loc in fault_locs:
                    if (fault_loc in group):
                        if (self._worst_effort and len(fault_locs) > 1):
                            worst_toRemove.append(fault_loc)
                            continue
                        # print("found fault", fault_num)
                        self.num_faults += 1
                        if (fault_loc not in seen_fault_locs):
                            seen_fault_locs.add(fault_loc)
                            self.fault_locs += 1
                        if (not faulty_group):
                            self.fault_groups += 1
                            faulty_group = True
                        # faults.remove(fault)
                        toRemove.add(fault_num)
                        break
                if (self._worst_effort):
                    for loc in worst_toRemove:
                        fault_locs.remove(loc)
            for fault in toRemove:
                self._faults.pop(fault)

    def __init__(self, spectrum, scores, worst_effort: bool):
        self.faults: Dict[int, List[Spectrum.Element]] = spectrum.get_faults()
        # needed to remove groups of fault locations
        faults = copy.deepcopy(self.faults)
        s_iter = iter(scores)
        self.ties: List[Ties.Tie] = []
        # Populate this Ties object
        s2 = next(s_iter, None)  # get the first element
        while (s2 is not None):
            score = s2.score
            tie = Ties.Tie(faults, worst_effort)
            # Get all UUTs with same score
            while (s2 is not None and s2.score == score):
                group = spectrum.get_group(s2.elem)
                tie.add_group(group)
                s2 = next(s_iter, None)
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
