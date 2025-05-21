from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking
from flitsr.advanced.artemis_impl import artemis
from flitsr.advanced.ranker import Ranker


class Artemis(Ranker):
    """
    Run the ARTEMIS technique on the spectrum to produce the ranked lists.
    This option may be combined with FLITSR and parallel to produce a
    hybrid technique.
    """
    def __init__(self, numUniverse: int = 17, maxUniverse: int = 20,
                 p: float = 1e-5):
        self.numUniverse = numUniverse
        self.maxUniverse = maxUniverse
        self.p = p

    def rank(self, spectrum: Spectrum, metric: str) -> Ranking:
        # Set default metric
        if (metric == 'artemis'):
            metric = 'ochiai'
        elements = spectrum.groups()
        matrix, errVector = spectrum.to_matrix()
        rankingList = artemis.explorer(matrix, errVector, spectrum.locs(),
                                       metric, self.numUniverse,
                                       self.maxUniverse, self.p)
        sortedRankingList = artemis.merge(rankingList, spectrum.locs())
        ranking = Ranking()
        for (elem_ind, score, _) in sortedRankingList:
            ranking.append(elements[int(elem_ind)], score, 0)
        return ranking
