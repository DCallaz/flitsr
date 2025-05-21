from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr import advanced


class SpectrumRefiner(ABC):
    @abstractmethod
    def refine(self, spectrum: Spectrum, method_lvl=False) -> Spectrum:
        pass

    def __init_subclass__(cls):
        advanced.register_refiner(cls)
