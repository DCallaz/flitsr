from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking
from flitsr.artemis_impl import artemis
import numpy as np


def run_artemis(spectrum: Spectrum, metric: str, numUniverse=17,
                maxUniverse=20, p=1e-5) -> Ranking:
    # Set default metric
    if (metric == 'artemis'):
        metric = 'ochiai'
    elements = spectrum.groups()
    matrix, errVector = spectrum.to_matrix()
    rankingList = artemis.explorer(matrix, errVector, spectrum.locs(),
                                   metric, numUniverse, maxUniverse, p)
    sortedRankingList = artemis.merge(rankingList, spectrum.locs())
    ranking = Ranking()
    for (elem_ind, score, _) in sortedRankingList:
        ranking.append(elements[int(elem_ind)], score, 0)
    return ranking
