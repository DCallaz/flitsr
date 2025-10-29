import random
from typing import List, Set, Optional, Dict, Iterator, Iterable, Any
from enum import Enum, auto
from flitsr.spectrum import Spectrum
from flitsr.errors import warning
import copy


class Tiebrk(Enum):
    """ An `Enum` for the tie-breaking method to be used. """

    EXEC = auto()
    """ Tie break only using execution counts. """

    RNDM = auto()
    """ Tie break randomly. Note, this will cause non-deterministic output. """

    ORIG = auto()
    """ Tie break using the original SBFL ranking, then execution counts. """


class Rank:
    """
    An `Entity <flitsr.spectrum.Spectrum.Entity>` from a spectrum, together
    with its score and execution count.
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
    """
    A singular ranking, containing ranked `Spectrum.Entity
    <flitsr.spectrum.Spectrum.Entity>`.
    """

    def __init__(self, tiebrk: Tiebrk = Tiebrk.ORIG):
        self._ranks: List[Rank] = []
        self._tiebrk = tiebrk
        self.entity_map: Dict[Spectrum.Entity, Rank] = {}
        self.place = 0

    def __getitem__(self, index: int):
        return self._ranks[index]

    def get_rank(self, entity: Spectrum.Entity, check_sub_group=False) -> Rank:
        """
        Return the `Rank` of the given `Spectrum.Entity
        <flitsr.spectrum.Spectrum.Entity>`. If the `check_sub_group`
        option is given, try to find if the given entity is contained within
        another group in the ranking (either as a sub-group or as an element).

        Args:
          entity: Spectrum.Entity: The entity to return the rank for
          check_sub_group:  (Default value = False) Whether to check for the
          `entity` as a subgroup of entities in the ranking.

        Returns:
          The `Rank` of the given entity.

        """
        try:
            return self.entity_map[entity]
        except KeyError as keyerror:
            if (check_sub_group):
                # Before exiting, first check if we can find a super-group
                is_group = isinstance(entity, Spectrum.Group)
                for key in self.entity_map:
                    # If a group, check if it is a sub-group
                    if (is_group):
                        if (isinstance(key, Spectrum.Group) and
                            key.is_subgroup(entity)):  # type:ignore
                            return self.entity_map[key]
                    # If an element, check if in any group
                    elif (entity in key):
                        return self.entity_map[key]
            # if no super-group can be found, raise the KeyError
            raise keyerror

    def sort(self, reverse: bool):
        """
        Re-sort this `Ranking` in-place by their scores, using the `Tiebrk`
        method set.

        Args:
          reverse: bool: Whether to sort by reverse order of scores.
        """
        if (self._tiebrk == Tiebrk.EXEC):  # Sorted by execution counts
            self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
        elif (self._tiebrk == Tiebrk.RNDM):  # random ordering
            random.shuffle(self._ranks)
        elif (self._tiebrk == Tiebrk.ORIG):  # original ranking tie break
            if (orig is not None):  # sort by original rank then exec count
                try:
                    self._ranks.sort(key=lambda x:
                                     orig.get_rank(x.entity, True).exec,
                                     reverse=reverse)
                    self._ranks.sort(key=lambda x:
                                     orig.get_rank(x.entity, True).score,
                                     reverse=reverse)
                except KeyError:
                    # if sorting by orig fails, print a warning and continue
                    warning("Could not sort by original ranking, despite it "
                            "being set")
                    pass
            else:  # if no orig, still sort by current execution count
                self._ranks.sort(key=lambda x: x.exec, reverse=reverse)
        self._ranks.sort(key=lambda x: x.score, reverse=reverse)

    def append(self, entity: Spectrum.Entity, score: float, exec_count: int):
        """
        Append the given `entity` to the ranking, with the given `score` and
        execution count `exec_count`.

        Args:
          entity: Spectrum.Entity: The entity to append to this `Ranking`.
          score: float: The score of the given `entity`.
          exec_count: int: The execution count of the given `entity`.
        """
        created = Rank(entity, score, exec_count)
        self._ranks.append(created)
        self.entity_map[entity] = created

    def extend(self, ranks: List[Rank]):
        """
        Extend this `Ranking` by adding all `Rank` in the `List` `ranks`.

        Args:
          ranks: List[Rank]: The `List` of ranks to add to this `Ranking`.
        """
        self._ranks.extend(ranks)
        for rank in ranks:
            self.entity_map[rank.entity] = rank

    def has_entity(self, entity: Spectrum.Entity) -> bool:
        """
        Return whether this `Ranking` contains the given `entity`. Does not
        check if the entity is a subgroup.

        Args:
          entity: Spectrum.Entity: The entity to check for.

        Returns:
          True if `entity` is directly in this `Ranking`, False otherwise.
        """
        return entity in self.entity_map

    def __iter__(self):
        return iter(self._ranks)

    def __len__(self):
        return len(self._ranks)

class Rankings:
    """
    A collection of `Ranking` objects, which share a non-overlapping set of
    elements from a `Spectrum <flitsr.spectrum.Spectrum>`.
    """
    def __init__(self, faults: Dict[Any, Set[Spectrum.Element]],
                 elements: List[Spectrum.Element],
                 rankings: Optional[Iterable[Ranking]] = None):
        self._faults = faults
        self._all_elems = elements
        self._rankings: List[Ranking] = []
        if (rankings is not None):
            self._rankings.extend(rankings)

    def faults(self) -> Dict[Any, Set[Spectrum.Element]]:
        """
        Return a dictionary of all faults in these rankings. See
        `Spectrum.get_faults <flitsr.spectrum.Spectrum.get_faults>` for a
        description of the return value.
        """
        return copy.deepcopy(self._faults)

    def elements(self) -> List[Spectrum.Element]:
        """ Return the global list of elements for all rankings. """
        return self._all_elems

    def rankings(self) -> List[Ranking]:
        """ Return a list of all the `Ranking`. """
        return self._rankings

    def append(self, ranking: Ranking):
        """
        Append the given `ranking` to this collection.

        Args:
          ranking: Ranking: The ranking to add.
        """
        self._rankings.append(ranking)

    def __iter__(self) -> Iterator:
        return iter(self._rankings)

    def __len__(self) -> int:
        return len(self._rankings)


orig: Optional[Ranking] = None


def set_orig(ranking: Ranking):
    """
    Set the original SBFL `Ranking` to be used in tie-breaking (see `Tiebrk`).
    Args:
      ranking: Ranking:

    Returns:

    """
    global orig
    orig = copy.deepcopy(ranking)


def unset_orig():
    """ """
    global orig
    orig = None
