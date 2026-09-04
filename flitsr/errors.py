import sys
from typing import NoReturn


def error(*args, **kwargs) -> NoReturn:
    """
    Print an error message and exit FLITSR. All arguments and keyword-arguments
    given are in the format of the Python print statement
    """
    print("ERROR:", end=' ', file=sys.stderr)
    print(*args, **kwargs, file=sys.stderr)
    quit()


def warning(*args, **kwargs) -> None:
    """
    Print a warning message and continue. All arguments and keyword-arguments
    given are in the format of the Python print statement
    """
    print("WARNING:", end=' ', file=sys.stderr)
    print(*args, **kwargs, file=sys.stderr)
