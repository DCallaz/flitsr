from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr import input

class Input(ABC):
    def __init_subclass__(cls):
        input.register_input(cls)

    @abstractmethod
    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        pass

    @staticmethod
    @abstractmethod
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
        for input_enum in list(input.InputType):
            input_cls = input_enum.value
            if (input_cls.check_format(input_path)):
                input_ins = input_cls()
                return input_ins.read_spectrum(input_path, split_faults,
                                               method_level)
        raise ValueError(f'Could not find reader for input file: {input_path}')
