import re
import inspect
from os import path as osp
from typing import List, final, Type, overload, Optional
from abc import ABC, abstractmethod
from deprecated.sphinx import versionadded, versionchanged, deprecated
from flitsr.spectrum import Spectrum
from flitsr.input.spectrumBuilder import SpectrumBuilder
from flitsr.input import BaseInputType
from flitsr.input.duplicates import DuplicateStrategy as DupStrat
from flitsr import input


class Input(ABC):
    """
    An abstract spectral input type. If extending from this type, see
    `DirInput` and `FileInput`.
    """
    @final
    def __init_subclass__(cls, /, register: bool = True, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (register):
            input.register_input(cls)

    @versionchanged(version='2.5.0', reason='Added the `split_faults`, '
                    '`method_level`, and `duplicate_strategy` parameters')
    @final
    def __init__(self, split_faults: bool = False, method_level: bool = False,
                 duplicate_strategy: DupStrat = DupStrat.REFUSE,
                 compute_groups: Optional[bool] = None):
        """
        Internal constructor for an `Input` type.

        Caution:
          This constructor should not be called directly. Use the `read_in`
          method instead.
        """
        self.method_level = method_level
        self.duplicate_strategy = duplicate_strategy
        self.split_faults = split_faults
        self.compute_groups = compute_groups
        self.sb = SpectrumBuilder(method_level, split_faults,
                                  duplicate_strategy, compute_groups)

    @staticmethod
    def get_run_file_name(input_path: str) -> str:
        """
        Return the name of the run file that this input type determines for
        the given input string. Note: this function assumes the given string is
        a valid input of a particular type, and thus is either a file or
        directory which represents a single program spectrum.

        Args:
          input_path: str: The name of the input file representing a single
            program spectrum.

        Returns:
          The name of the run file. For files, this is just the input file name
          with the extension replaced with ".run". For directories, this is the
          name of the directory with the ".run" extension appended.

        """
        if (osp.sep in input_path or osp.isdir(input_path)):  # dir-type inputs
            return input_path.split(osp.sep)[0] + ".run"
        else:  # file-type inputs
            return re.sub("\\.\\w+$", ".run", input_path)

    @overload
    @classmethod
    def read_spectrum(cls, input_path: str) -> Spectrum: ...

    @overload
    @classmethod
    def read_spectrum(cls, input_path: str, split_faults: bool = False,
                      method_level: bool = False, duplicate_strategy:
                      DupStrat = DupStrat.REFUSE, compute_groups:
                      Optional[bool] = None) -> Spectrum: ...

    @classmethod
    @deprecated(version='2.5.0', reason='This method is deprecated and will '
                'be removed in a future release. Consider using the `read_in` '
                'method instead.')
    @final
    def read_spectrum(cls, *args, **kwargs) -> Spectrum:
        """
        Deprecated alias of `Input.read_in`.
        """
        return cls.read_in(*args, **kwargs)

    @versionadded(version='2.5.0')
    @abstractmethod
    def _read_spectrum(self, input_path: str) -> Spectrum:
        """
        Abstract method to facilitate reading in the spectrum. Any concrete
        class extending `~flitsr.input.Input` must implement this method.

        The method is called on a constructed `~flitsr.input.Input` object, which
        contains all options, as well an initialized `~flitsr.spectrumBuilder.SpectrumBuilder`
        object which may be used for constructing the spectrum. The
        `~flitsr.spectrumBuilder.SpectrumBuilder` object handles any advanced
        usage scenarios such as duplicates, method level collapsing, and fault
        splitting. Calling `~flitsr.spectrumBuilder.SpectrumBuilder.get_spectrum`
        will return the constructed `~flitsr.spectrum.Spectrum` object.

        Args:
          input_path: The path to the input file to read in.

        Returns:
          The spectrum that was read in.

        Note:
          Using the SpectrumBuilder object provided in ``self.sb`` to
          construct the Spectrum is strongly advised.
        """
        pass

    @classmethod
    def write_spectrum(cls, spectrum: Spectrum, output_path: str) -> None:
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
    @final
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

    @classmethod
    @final
    def read_in(cls, input_path: str, split_faults: bool = False,
                method_level: bool = False, duplicate_strategy:
                DupStrat = DupStrat.REFUSE,
                compute_groups: Optional[bool] = None) -> Spectrum:
        """
        Read in the spectrum from the given input file. When called from
        a concrete `Input` class, simply reads the spectrum using that input
        type. When called from `Input`, or any other abstract class,
        this method guesses the input type of the given input path out of all
        available input types, and reads in the spectrum using that input type.

        Args:
          input_path: The spectrum input path string to read in.
          split_faults: Whether to split faults using FLITSR's split_faults
            functionality.
          method_level: Whether to read this spectrum in as a method level
            spectrum.
          duplicate_strategy: The policy for allowing duplicate values in the
            spectrum.

        Returns:
          The spectrum that was read in.
        """
        if (inspect.isabstract(cls)):
            reader = Input.get_reader(input_path)
        else:
            reader = cls
        instance = reader(split_faults, method_level, duplicate_strategy,
                          compute_groups)
        return instance._read_spectrum(input_path)

    @staticmethod
    @final
    def get_reader(input_path: str) -> Type['Input']:
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
                return input_cls
        raise ValueError(f"Unknown input type \"{input_path}\"")

    @classmethod
    @abstractmethod
    @versionadded(version='2.5.0')
    def base_input_type(self) -> BaseInputType:
        """
        The type (file or directory) expected for this Input method. For
        convenience in implementing this method, extend either `FileInput` or
        `DirInput`.
        """
        pass

    @classmethod
    def search_pattern(self, **kwargs) -> str:
        """
        Returns the search pattern to use in the `run_all` script when
        searching for inputs of the given `Input` type to run on. The format is
        a Unix shell style pattern (see `fnmatch`).

        For `FileInput` types, will be the pattern to match against the name of
        the file, for `DirInput` types, will match against the name of any file
        within the directory.

        The default is "*", i.e., match any file, but may be overriden by any
        `Input` sub-class. Sub-classes may also define optional arguments which
        can be used to render specialized patterns.
        """
        return "*"


class FileInput(Input, register=False):
    """
    An abstract spectral input type which reads in from files. This class is
    provided as a convenience for extending `Input`, with the `base_input_type`
    function set to return `BaseInputType.FILE`.
    """
    @classmethod
    @final
    def base_input_type(self) -> BaseInputType:
        return BaseInputType.FILE


class DirInput(Input, register=False):
    """
    An abstract spectral input type which reads in from directories. This class
    is provided as a convenience for extending `Input`, with the
    `base_input_type` function set to return `BaseInputType.DIR`.
    """
    @classmethod
    @final
    def base_input_type(self) -> BaseInputType:
        return BaseInputType.DIR
