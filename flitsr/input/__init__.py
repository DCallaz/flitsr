from abc import ABC, abstractmethod
import importlib
import pkgutil
from enum import Enum
from flitsr.spectrum import Spectrum
from flitsr import input

_inputs = {}

def register_input(cls):
    _inputs[cls.__name__.upper()] = cls

__all__ = [m[1] for m in pkgutil.iter_modules(input.__path__)]
for module in __all__:
    importlib.import_module('.'+module, package=__name__)

InputType = Enum('InputType', _inputs,  # type:ignore
                   module=input, qualname='input.InputType')

class Input(ABC):
    @abstractmethod
    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        pass

    @abstractmethod
    @staticmethod
    def check_format(input_path: str) -> bool:
        """
        Check whether the files from the specified input_path are of the
        concrete types format. This implementation of this abstract method
        must return a boolean, where True indicates that the input is in the
        format recognized by the implementing class, and False otherwise
        """
        pass

    @staticmethod
    def read_in(input_path: str, split_faults: bool,
                method_level=False) -> Spectrum:
        for input_enum in InputType:
            input_cls = input_enum.value
            if (input_cls.check_format(input_path)):
                return input_cls.read_spectrum(input_path, split_faults,
                                               method_level)
        raise ValueError(f'Could not find reader for input file: {input_path}')
