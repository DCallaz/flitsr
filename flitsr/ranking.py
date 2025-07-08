import random
from typing import List, Set, Optional, Dict, Iterator, Iterable, Any
from enum import Enum, auto
from flitsr.spectrum import Spectrum
import copy


class Tiebrk(Enum):
    EXEC = auto()
    RNDM = auto()
    ORIG = auto()


class Rank:
    """
    A group from a spectrum, together with its scores.
    """
    def __init__(self, entity: Spectrum.Entity, score: float,
                 exec_count: int):
        self.entity = entity
        self.score = score
        self.exec = exec_count

    def __str__(self):
        return "(" + str(self.entity) + ", " + str(self.score) + ")"

    def __repr__(self):
        return str(self)


class Ranking:
    def __init__(self, tiebrk: Tiebrk = Tiebrk.ORIG):
        self._ranks: List[Rank] = []
        self._tiebrk = tiebrk
        self.entity_map: Dict[Spectrum.Entity, Rank] = {}
        self.place = 0

    def __getitem__(self, index: int):
        return self._ranks[index]

    def get_rank(self, entity: Spectrum.Entity) -> Rank:
        return self.entity_map[entity]

    def sort(self, reverse: bool):
        if (self._tiebrk == Tiebrk.EXEC):  # Sorted by execution counts
            self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
        elif (self._tiebrk == Tiebrk.RNDM):  # random ordering
            random.shuffle(self._ranks)
        elif (self._tiebrk == Tiebrk.ORIG):  # original ranking tie break
            if (orig is not None):  # sort by original rank then exec count
                self._ranks.sort(key=lambda x: orig.get_rank(x.entity).exec,
                                 reverse=reverse)
                self._ranks.sort(key=lambda x: orig.get_rank(x.entity).score,
                                 reverse=reverse)
            else:  # if no orig, still sort by current execution count
                self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
        self._ranks.sort(key=lambda x: x.score, reverse=reverse)

    def append(self, entity: Spectrum.Entity, score: float, exec_count: int):
        created = Rank(entity, score, exec_count)
        self._ranks.append(created)
        self.entity_map[entity] = created

    def extend(self, ranks: List[Rank]):
        self._ranks.extend(ranks)
        for rank in ranks:
            self.entity_map[rank.entity] = rank

    def has_entity(self, entity: Spectrum.Entity) -> bool:
        return entity in self.entity_map

    def __iter__(self):
        return iter(self._ranks)

    def __len__(self):
        return len(self._ranks)

class Rankings:
    def __init__(self, faults: Dict[Any, Set[Spectrum.Element]],
                 elements: List[Spectrum.Element],
                 rankings: Optional[Iterable[Ranking]] = None):
        self._faults = faults
        self._all_elems = elements
        self._rankings: List[Ranking] = []
        if (rankings is not None):
            self._rankings.extend(rankings)

    def faults(self) -> Dict[Any, Set[Spectrum.Element]]:
        return copy.deepcopy(self._faults)

    def elements(self) -> List[Spectrum.Element]:
        return self._all_elems

    def rankings(self) -> List[Ranking]:
        return self._rankings

    def append(self, ranking: Ranking):
        self._rankings.append(ranking)

    def __iter__(self) -> Iterator:
        return iter(self._rankings)

    def __len__(self) -> int:
        return len(self._rankings)


orig: Optional[Ranking] = None


def set_orig(ranking: Ranking):
    global orig
    orig = copy.deepcopy(ranking)


def unset_orig():
    global orig
    orig = None
