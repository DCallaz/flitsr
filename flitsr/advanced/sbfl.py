from flitsr.ranking import Ranking, Tiebrk
from flitsr.advanced.ranker import Ranker
from flitsr.advanced.attributes import existing, print_name
from flitsr.spectrum import Spectrum
from flitsr.suspicious import Suspicious


@print_name('base')
class SBFL(Ranker):
    """
    Disables the FLITSR algorithm so that only the base metric
    is used to produce the ranking. This is equivalent to using the
    base metric as-is, but allows the user to run these metrics
    within the FLITSR framework
    """

    @existing('tiebrk')
    def __init__(self, tiebrk: Tiebrk = Tiebrk.ORIG):
        self.tiebrk = tiebrk

    def rank(self, spectrum: Spectrum, base_metric: str) -> Ranking:
        return Suspicious.apply_formula(spectrum, base_metric,
                                        tiebrk=self.tiebrk)
