from __future__ import annotations
from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking
from flitsr import advanced


class Ranker(ABC):
    """
    A `Ranker` technique takes a `Spectrum <flitsr.spectrum.Spectrum>` and
    forms a `Ranking <flitsr.ranking.Ranking>` of the elements in the the
    spectrum.
    """

    @abstractmethod
    def rank(self, spectrum: Spectrum, base_metric: str) -> Ranking:
        """
        Provides the ranking functionality for the `Ranker`. Takes a `Spectrum
        <flitsr.spectrum.Spectrum>` and a `base_metric` and returns a `Ranking
        <flitsr.ranking.Ranking>` of the elements in the spectrum. Note that the
        technique does not need to use the `base_metric`.

        Args:
          spectrum: Spectrum: The spectrum whose elements to rank
          base_metric: str: The name of the SBFL metric to optionally use within
            the technique to rank the elements.

        Returns:
          A `Ranking <flitsr.ranking.Ranking>` of the elements in the
          `spectrum`.
        """
        pass

    def __init_subclass__(cls):
        advanced.register_ranker(cls)
