from enum import Enum, auto
from argparse import ArgumentTypeError


class DuplicateStrategy(Enum):
    ALLOW = auto()
    IGNORE = auto()
    REFUSE = auto()

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return DuplicateStrategy[s]
        except KeyError:
            choices = ', '.join(f"'{d}'" for d in list(DuplicateStrategy))
            raise ArgumentTypeError(f"invalid choice: '{s}' "
                                    f"(choose from {choices})")
