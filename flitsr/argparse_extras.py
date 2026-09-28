import argparse


class BooleanOptionalAction(argparse.Action):
    """
    Copied (almost) verbatim from the argparse library code available after
    Python version 3.9. Implements the same functionality before 3.9, and can
    be replaced by argparse.BooleanOptionalAction when flitsr does not support
    versions < 3.9 anymore.
    """
    def __init__(self, option_strings, dest, default=None, required=False,
                 help=None, deprecated=False):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if option_string.startswith('--'):
                if option_string.startswith('--no-'):
                    raise ValueError(f'invalid option name {option_string!r} '
                                     f'for BooleanOptionalAction')
                option_string = '--no-' + option_string[2:]
                _option_strings.append(option_string)

        super().__init__(option_strings=_option_strings, dest=dest, nargs=0,
                         default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith('--no-'))

    def format_usage(self):
        return ' | '.join(self.option_strings)
