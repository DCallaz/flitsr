from abc import ABC, abstractmethod
from typing import List
from flitsr.spectrum import Spectrum
from flitsr import advanced


class Cluster(ABC):
    @abstractmethod
    def cluster(self, inp_file: str, spectrum: Spectrum,
                method_lvl=False) -> List[Spectrum]:
        pass

    def __init_subclass__(cls):
        advanced.register_cluster(cls)
