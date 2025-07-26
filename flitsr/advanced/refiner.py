from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr import advanced


class Refiner(ABC):
    """ A `Refiner` technique takes a `Spectrum <flitsr.spectrum.Spectrum>` and
    manipulates and extends it, returning a modified spectrum."""

    @abstractmethod
    def refine(self, spectrum: Spectrum, method_lvl=False) -> Spectrum:
        """
        Provides the functionality for the `Refiner`. Takes a `Spectrum
        <flitsr.spectrum.Spectrum>` and manipulates or extends it, returning a
        modified spectrum.

        Args:
          spectrum: Spectrum: The input `Spectrum <flitsr.spectrum.Spectrum>`
          method_lvl:  (Default value = False) Whether the input `spectrum`
            refers to a method level spectrum.

        Returns:
          The modified `Spectrum<flitsr.spectrum.Spectrum>`.

        """
        pass

    def __init_subclass__(cls):
        advanced.register_refiner(cls)
