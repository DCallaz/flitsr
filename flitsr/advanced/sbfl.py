from flitsr.ranking import Ranking
from flitsr.advanced.ranker import Ranker
from flitsr.spectrum import Spectrum
from flitsr.suspicious import Suspicious


class SBFL(Ranker):
    """
    Disables the FLITSR algorithm so that only the base metric
    is used to produce the ranking. This is equivalent to using the
    base metric as-is, but allows the user to run these metrics
    within the FLITSR framework
    """
    _print_name = 'base'

    _tiebrk_opts = ['exec', 'rndm', 'orig']

    def __init__(self, tiebrk: str = 'orig'):
        self.tiebrk = self._tiebrk_opts.index(tiebrk) + 1
        pass

    def rank(self, spectrum: Spectrum, base_metric: str) -> Ranking:
        return Suspicious.apply_formula(spectrum, base_metric,
                                        tiebrk=self.tiebrk)
