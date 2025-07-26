# PYTHON_ARGCOMPLETE_OK
import sys
from os import path as osp
from typing import List, Optional
from argparse import ArgumentParser
import argcomplete
from enum import Enum
from flitsr.errors import error
from flitsr.input.input_reader import Input
from flitsr.input import InputType


def convert(input_file: str, output_format: Optional[InputType] = None,
            output_file: Optional[str] = None):
    """Convert a input file from one spectral format to another"""
    # Check the input file type and set input method
    try:
        reader = Input.get_reader(input_file)
    except ValueError as e:
        error(e)
    input_format = reader.get_type()
    spectrum = reader.read_spectrum(input_file, False)
    # Set the output method if necessary
    if (output_format is None):
        if (input_format is InputType['TCM']):
            output_format = InputType['GZOLTAR']
        else:
            output_format = InputType['TCM']
    # Set the output file name if necessary
    if (output_file is None):
        output_file = osp.splitext(input_file)[0] + (".tcm" if output_format is
                                                     InputType['TCM'] else "")
    if (output_file == input_file):
        error(f"Cannot override input file {input_file} with output")
    # Print out the spectrum in the converted format
    output_format.value.write_spectrum(spectrum, output_file)


def get_parser() -> ArgumentParser:
    parser = ArgumentParser('transform', description='Transform a spectrum '
                            'from one format to another')
    parser.add_argument('input', help='The spectrum input file. The spectral '
                        'format is guessed from the input file, and by '
                        'default the output format is assumed to be a '
                        'different format type.')
    output_types = [it.name for it in list(InputType)]
    parser.add_argument('-t', '--output-type', help='Convert the input file'
                        'into the given output format', choices=output_types)
    parser.add_argument('-o', '--output-file', help='Specifies the name of '
                        'the output file. By default, the name is derived '
                        'from the name of the input file; for example, if the '
                        'input file is "input.tcm", and the output format is '
                        'Gzoltar, the output will be "input/".')
    argcomplete.autocomplete(parser)
    return parser


def main(argv: Optional[List[str]] = None):
    parser = get_parser()
    args = parser.parse_args(argv)
    if (args.output_type is not None):
        args.output_type = InputType[args.output_type]
    convert(args.input, args.output_type, args.output_file)


if __name__ == "__main__":
    main()
