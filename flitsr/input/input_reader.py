from typing import List
from abc import ABC, abstractmethod
from flitsr.spectrum import Spectrum
from flitsr import input


class Input(ABC):
    """ An abstract spectral input type """
    def __init_subclass__(cls):
        input.register_input(cls)

    @abstractmethod
    def get_run_file_name(self, input_path: str):
        """
        Return the name of the run file that this input type determines for
        the given input string.

        Args:
          input_path: str: The name of the input file.

        Returns:
          The name of the run file.

        """
        pass

    @abstractmethod
    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        """
        Read in the spectrum from the given input file using this input type.

        Args:
          input_path: str: The path string of the input spectrum.
          split_faults: bool: Whether to split faults using FLITSR's
                        split_faults functionality.
          method_level:  (Default value = False) Whether to read this spectrum
                        in as a method level spectrum.

        Returns:
          The spectrum that was read in.

        """
        pass

    @classmethod
    def write_spectrum(cls, spectrum: Spectrum, output_path: str):
        """
        Write the given spectrum in the format of this input type. NOTE: this
        method does not need to be implemented by an input type. If it is not
        implemented and this method is called, a NotImplementedError will be
        thrown.

        Args:
          spectrum: Spectrum: The spectrum to write.
          output_path: str: The output path location string.

        """
        raise NotImplementedError("Cannot write spectrum in"
                                  f"{cls.__name__} format")

    @classmethod
    def get_elem_separators(cls) -> List[str]:
        """
        Method to get the separators used for printing out elements when
        writing a spectrum in the format of this input type. NOTE: this method
        does not need to be implemented by an input type unless it is used in
        the implemented write_spectrum method.
        """
        raise NotImplementedError(f"Input type {cls.__name__} not supported "
                                  "for output string")

    @classmethod
    def get_type(cls) -> 'input.InputType':
        """ Return the InputType enum of this input type. """
        return input.InputType[cls.__name__.upper()]

    @staticmethod
    @abstractmethod
    def check_format(input_path: str) -> bool:
        """
        Check whether the files from the specified input_path are of the
        concrete types format. The implementation of this abstract method
        must return a boolean, where True indicates that the input is in the
        format recognized by the implementing class, and False otherwise

        Args:
          input_path: str: The input path to check for format.

        Returns:
          True if the input path refers to input in the format that this input
          type can read, or False otherwise.

        """
        pass

    @staticmethod
    def read_in(input_path: str, split_faults: bool,
                method_level=False) -> Spectrum:
        """
        Static helper method that guesses the input type of the given input
        path out of all available input types, and reads in the spectrum using
        that input type.

        Args:
          input_path: str: The spectrum input path string to read in.
          split_faults: bool: Whether to split faults using FLITSR's
                        split_faults functionality.
          method_level:  (Default value = False) Whether to read this spectrum
                        in as a method level spectrum.

        Returns:
          The spectrum that was read in.

        """
        reader = Input.get_reader(input_path)
        return reader.read_spectrum(input_path, split_faults,
                                    method_level)

    @staticmethod
    def get_reader(input_path: str) -> 'Input':
        """
        Static helper method that guesses the input type of the given input
        path out of all available input types.

        Args:
          input_path: str: The input path string to guess the input type for.

        Returns:
          The concrete input type that can read in the given input path.

        """
        for input_enum in list(input.InputType):
            input_cls = input_enum.value
            if (input_cls.check_format(input_path)):
                return input_cls()
        raise ValueError(f"Unknown input type \"{input_path}\"")
