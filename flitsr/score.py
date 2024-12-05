import random
from typing import List, Optional, Dict
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

    def __getitem__(self, index: int):
        return self._scores[index]

    def get_score(self, elem):
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
                self._scores.sort(key=lambda x: orig.get_score(x.elem).exec,
                                  reverse=reverse)
                self._scores.sort(key=lambda x: orig.get_score(x.elem).score,
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


orig: Optional[Scores] = None


def set_orig(scores: Scores):
    global orig
    orig = copy.deepcopy(scores)


def unset_orig():
    global orig
    orig = None
