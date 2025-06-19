from typing import List
from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr import input


class Input(ABC):
    def __init_subclass__(cls):
        input.register_input(cls)

    @abstractmethod
    def get_run_file_name(self, input_path: str):
        pass

    @abstractmethod
    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        pass

    @classmethod
    def write_spectrum(cls, spectrum: Spectrum, output_path: str):
        raise NotImplementedError("Cannot write spectrum in"
                                  f"{cls.__name__} format")

    @classmethod
    def get_elem_separators(cls) -> List[str]:
        raise NotImplementedError(f"Input type {cls.__name__} not supported "
                                  "for output string")

    @classmethod
    def get_type(cls) -> 'input.InputType':
        return input.InputType[cls.__name__.upper()]

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
        reader = Input.get_reader(input_path)
        return reader.read_spectrum(input_path, split_faults,
                                    method_level)

    @staticmethod
    def get_reader(input_path: str) -> 'Input':
        for input_enum in list(input.InputType):
            input_cls = input_enum.value
            if (input_cls.check_format(input_path)):
                return input_cls()
        raise ValueError(f"Unknown input type \"{input_path}\"")
