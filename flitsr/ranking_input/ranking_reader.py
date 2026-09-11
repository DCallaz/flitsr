import re
from abc import ABC, abstractmethod
from typing import TextIO, Type, Union, final

from flitsr import ranking_input
from flitsr.errors import error
from flitsr.ranking import Rankings


class RankingInput(ABC):
    """
    An abstract ranking input type.
    """
    @final
    def __init_subclass__(cls, /, register: bool = True, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (register):
            ranking_input.register_ranking_input(cls)

    @final
    @classmethod
    def read_any_ranking(cls, ranking_file: Union[str, TextIO],
                         method_level=False) -> Rankings:
        """
        Guess the ranking from the contents of the `ranking_file` and read it
        in. Closes the file after reading (even if an open file handle is
        given).

        Args:
          ranking_file: str: The ranking input file to read in.
          method_level:  (Default value = False) Whether the ranking file is
            method level.

        Returns:
          A `Rankings <flitsr.ranking.Rankings>` object containing the read-in
          ranking(s).
        """
        with (open(ranking_file) if isinstance(ranking_file, str)
              else ranking_file) as rinput:
            try:
                rank_reader = cls.get_ranking_reader(rinput)
                return rank_reader._read_ranking(rinput)
            except Exception as e:  # noqa
                error(f"{type(e).__name__} exception occurred while reading "
                      f"in ranking \"{ranking_file}\": {e}")

    @final
    @staticmethod
    def get_ranking_reader(rinput: TextIO) -> Type['RankingInput']:
        """
        Static helper method that guesses the ranking input type of the given
        input path out of all available ranking input types.

        Args:
          input_path: str: The input stream to guess the type for.

        Returns:
          The concrete ranking input type that can read in the given input.

        Note:
          This method ensures that it leaves the `rinput` stream as it found it
          -- with the stream position back at the start of the stream.
        """
        rinput.seek(0)  # sanity check
        for rinput_enum in list(ranking_input.RankingInputType):
            rinput_cls = rinput_enum.value
            if (rinput_cls._check_format(rinput)):
                rinput.seek(0)  # reset input before returning
                return rinput_cls
            rinput.seek(0)  # reset input before trying next
        raise ValueError(f"Unknown ranking input type \"{rinput.name}\"")

    @classmethod
    @abstractmethod
    def _read_ranking(cls, ranking_file: TextIO) -> Rankings:
        """
        Abstract method for reading in the given ranking in the format of this
        `~flitsr.ranking_input.RankingInput` type.

        Args:
          ranking_file: The ranking file to read in.

        Returns:
          A `~flitsr.ranking.Rankings` object constructed from the
          corresponding `ranking_file` input.
        """

    @staticmethod
    @abstractmethod
    def _check_format(ranking_file: TextIO) -> bool:
        """
        Check whether the given ranking file is in a format readable by this
        ranking type. The implementation of this abstract method must return a
        boolean, where True indicates that the input is in the format
        recognized by the implementing class, and False otherwise.

        Args:
          ranking_file: The ranking input file to check for format.

        Returns:
          True if the input refers to a ranking in the format that this
          ranking input type can read, or False otherwise.

        Note:
          This method should only return True if the given ranking file is
          DEFINITELY in a format recognizable by this ranking input type. It
          should not return true only if it *could* be.
        """
