# PYTHON_ARGCOMPLETE_OK
import sys
from os import path as osp
from typing import List, Optional
from argparse import ArgumentParser
from enum import Enum
from flitsr.errors import error
from flitsr.output import print_tcm, print_gzoltar
from flitsr.input_type import InputType


def convert(input_file: str, output_format: Optional[InputType] = None,
            output_file: Optional[str] = None):
    """Convert a input file from one spectral format to another"""
    # Check the input file type and set input method
    if (osp.isfile(input_file)):
        from flitsr.tcm_input import read_spectrum
        input_format = InputType.TCM
    elif (osp.isdir(input_file) and
          osp.isfile(osp.join(input_file, "matrix.txt"))):
        from flitsr.input import read_spectrum
        input_format = InputType.GZOLTAR
    else:
        error("Could not determine input spectral format, exiting...")
    spectrum = read_spectrum(input_file, False)
    # Set the output method if necessary
    if (output_format is None):
        if (input_format is InputType.TCM):
            output_format = InputType.GZOLTAR
        elif (input_format is InputType.GZOLTAR):
            output_format = InputType.TCM
    # Set the output file name if necessary
    if (output_file is None):
        output_file = osp.splitext(input_file)[0] + (".tcm" if output_format is
                                                     InputType.TCM else "")
    if (output_file == input_file):
        error(f"Cannot override input file {input_file} with output")
    # Print out the spectrum in the converted format
    if (output_format is InputType.TCM):
        print_tcm(spectrum, open(output_file, 'w'))
    elif (output_format is InputType.GZOLTAR):
        print_gzoltar(spectrum, output_file)


def main(argv: Optional[List[str]] = None):
    parser = ArgumentParser('transform', description='Transform a spectrum '
                            'from one format to another')
    parser.add_argument('input', help='The spectrum input file. The spectral '
                        'format is guessed from the input file, and by '
                        'default the output format is assumed to be a '
                        'different format type.')
    parser.add_argument('-t', '--tcm', action='store_true',
                        help='Convert input file into TCM format')
    parser.add_argument('-g', '--gzoltar', action='store_true',
                        help='Convert input file into Gzoltar format')
    parser.add_argument('-o', '--output-file', help='Specifies the name of '
                        'the output file. By default, the name is derived '
                        'from the name of the input file; for example, if the '
                        'input file is "input.tcm", and the output format is '
                        'Gzoltar, the output will be "input/".')
    args = parser.parse_args(argv)
    if (args.tcm):
        output_type = InputType.TCM
    elif (args.gzoltar):
        output_type = InputType.GZOLTAR
    else:
        output_type = None
    convert(args.input, output_type, args.output_file)


if __name__ == "__main__":
    main()
