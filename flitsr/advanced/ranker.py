from __future__ import annotations
from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking
from flitsr import advanced


class Ranker(ABC):
    @abstractmethod
    def rank(self, spectrum: Spectrum, base_metric: str) -> Ranking:
        pass

    def __init_subclass__(cls):
        advanced.register_ranker(cls)
