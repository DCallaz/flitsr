import random
from typing import List, Optional, Dict
from flitsr.spectrum import Spectrum
import copy


class Rank:
    """
    A group from a spectrum, together with its scores.
    """
    def __init__(self, group: Spectrum.Group, score: float,
                 exec_count: int):
        self.group = group
        self.score = score
        self.exec = exec_count

    def __str__(self):
        return "(" + str(self.group) + ", " + str(self.score) + ")"

    def __repr__(self):
        return str(self)


class Ranking:
    def __init__(self, tiebrk: int = 3):
        self._ranks: List[Rank] = []
        self._tiebrk = tiebrk
        self.group_map: Dict[Spectrum.Group, Rank] = {}
        self.place = 0

    def __getitem__(self, index: int):
        return self._ranks[index]

    def get_rank(self, group: Spectrum.Group) -> Rank:
        return self.group_map[group]

    def sort(self, reverse: bool):
        if (self._tiebrk == 1):  # Sorted by execution counts
            self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
            self._ranks.sort(key=lambda x: x.score, reverse=reverse)
        elif (self._tiebrk == 2):  # random ordering
            random.shuffle(self._ranks)
            self._ranks.sort(key=lambda x: x.score, reverse=reverse)
        elif (self._tiebrk == 3):  # original ranking tie break
            if (orig is not None):  # sort by original rank then exec count
                self._ranks.sort(key=lambda x: orig.get_rank(x.group).exec,
                                 reverse=reverse)
                self._ranks.sort(key=lambda x: orig.get_rank(x.group).score,
                                 reverse=reverse)
            else:  # if no orig, still sort by current execution count
                self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
            self._ranks.sort(key=lambda x: x.score, reverse=reverse)
        else:
            self._ranks.sort(key=lambda x: x.score, reverse=reverse)

    def append(self, group: Spectrum.Group, score: float, exec_count: int):
        created = Rank(group, score, exec_count)
        self._ranks.append(created)
        self.group_map[group] = created

    def extend(self, ranks: List[Rank]):
        self._ranks.extend(ranks)
        for rank in ranks:
            self.group_map[rank.group] = rank

    def has_group(self, group: Spectrum.Group) -> bool:
        return group in self.group_map

    def __iter__(self):
        return iter(self._ranks)

    def __len__(self):
        return len(self._ranks)


orig: Optional[Ranking] = None


def set_orig(ranking: Ranking):
    global orig
    orig = copy.deepcopy(ranking)


def unset_orig():
    global orig
    orig = None
