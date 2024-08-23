from flitsr.spectrum import Spectrum
from flitsr.score import Scores
from flitsr.artemis_impl import artemis
import numpy as np


def run_artemis(spectrum: Spectrum, metric: str, numUniverse=17,
                maxUniverse=20, p=1e-5):
    # Set default metric
    if (metric == 'artemis'):
        metric = 'ochiai'
    matrix = np.zeros((len(spectrum.tests()), spectrum.locs()))
    errVector = np.zeros(len(spectrum.tests()))
    elements = spectrum.elements()
    for (i, test) in enumerate(spectrum.tests()):
        for (j, elem) in enumerate(elements):
            matrix[i][j] = spectrum[test][elem]
        errVector[i] = 1 if (test.outcome is False) else 0
    rankingList = artemis.explorer(matrix, errVector, spectrum.locs(),
                                   metric, numUniverse, maxUniverse, p)
    sortedRankingList = artemis.merge(rankingList, spectrum.locs())
    scores = Scores()
    for (elem_ind, score, _) in sortedRankingList:
        scores.append(elements[int(elem_ind)], score, 0)
    return scores
