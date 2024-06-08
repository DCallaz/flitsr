import random
from typing import Callable, List, Any, Optional
from flitsr.spectrum import Spectrum
import copy


class Scores:
    class Score:
        """
        A element from a spectrum, together with its scores.
        """
        def __init__(self, elem: Spectrum.Element, score, exec_count):
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

    def append(self, elem, score, exec_count):
        score = Scores.Score(elem, score, exec_count)
        self.scores.append(score)

    def __iter__(self):
        return iter(self.scores)

    def __next__(self):
        return next(self.scores)

    def __len__(self):
        return len(self.scores)


orig: Optional[Scores] = None


def set_orig(scores: Scores):
    global orig
    orig = copy.deepcopy(scores)


def unset_orig():
    global orig
    orig = None
