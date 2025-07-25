from abc import ABC, abstractmethod
from typing import List
from flitsr.spectrum import Spectrum
from flitsr import advanced


class Cluster(ABC):
    """ A `Cluster` technique takes a `Spectrum <flitsr.spectrum.Spectrum>` and
    returns a collection of spectra that are decompositions of the original"""

    @abstractmethod
    def cluster(self, inp_file: str, spectrum: Spectrum,
                method_lvl=False) -> List[Spectrum]:
        """
        Provides the clustering functionality of this `Cluster` technique. A
        `Cluster` takes a `Spectrum <flitsr.spectrum.Spectrum>` `spectrum` and
        returns a collection of spectra which are decompositions of the input
        spectrum.

        Args:
          inp_file: str: The input file for the input spectrum
          spectrum: Spectrum: The input spectrum
          method_lvl:  (Default value = False) Whether the input spectrum
            refers to a method level spectrum

        Returns:
          A collection of spectra which are decompositions of the input
          spectrum.
        """
        pass

    def __init_subclass__(cls):
        advanced.register_cluster(cls)
