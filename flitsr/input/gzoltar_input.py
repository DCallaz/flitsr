import sys
import re
import os
from os import path as osp
from typing import TextIO
from shutil import rmtree
from flitsr.spectrum import Spectrum, Outcome
from flitsr.input.spectrumBuilder import TestKeyError, ElemKeyError
from flitsr.errors import error
from flitsr.input.input_reader import DirInput


class Gzoltar(DirInput):
    @classmethod
    def search_pattern(self, **kwargs):
        """
        Returns the search pattern to use in the `run_all` script when
        searching for inputs of the `Gzoltar` type to run on. The format is a
        Unix shell style pattern (see `Input.search_pattern` for more details).

        Returns:
          The search pattern to use, which is always "spectra.csv".
        """
        return 'spectra.csv'

    def _construct_details(self, f: TextIO):
        """
        Fills the spectrum object with elements read in from the open file 'f'.
        """
        bugs = 0
        assert f.readline() == 'name\n'  # remove header
        for line in f:
            m = re.fullmatch('([^$]+)\\$([^#]+)#([^:]+):([0-9]+)(?::(.+))?',
                             line.rstrip())
            if (m is None):
                error("Incorrectly formatted line \"" + line +
                      "\" when reading input file")
            else:
                faults = []
                if (m.group(5) is not None):
                    bs = m.group(5).split(':')
                    if (not bs[0].isdigit()):
                        faults = [bugs]
                    else:
                        faults = []
                        for b in bs:
                            faults.append(int(b))
                    bugs += 1
                details = [m.group(1)+"."+m.group(2), m.group(3), m.group(4)]
                self.sb.addElement(details, faults)

    def _construct_tests(self, tests_reader: TextIO):
        tests_reader.readline()
        for line in tests_reader:
            m = re.fullmatch('([^,]+),(PASS|FAIL|ERROR)(,.*)?', line.rstrip())
            if (m is None):
                error("incorrectly formatted test line in input file:",
                      line, "terminating...")
            else:
                self.sb.addTest(m.group(1), Outcome[m.group(2)])

    def _fill_spectrum(self, bin_file: TextIO):
        for t, line in enumerate(bin_file):
            if (line == ''):
                error('Incorrect number of matrix lines', f'({t+1})',
                      'in input file, terminating...')
            arr = line.rstrip().split()
            # Loop over all elements in test exec (remove test outcome at end)
            for i in range(0, len(arr)-1):
                if (arr[i] != "0"):
                    try:
                        self.sb.addExecution(t, i)
                    except ElemKeyError:
                        error('Incorrect number of matrix columns',
                              f'({i+1})', 'in input file, terminating...')
                    except TestKeyError:
                        error('Incorrect number of matrix lines',
                              f'({t+1})', 'in input file, terminating...')

    def _read_spectrum(self, input_path: str) -> Spectrum:
        # Getting the details of the elements
        self._construct_details(open(input_path+"/spectra.csv"))
        # Getting the details of the tests
        self._construct_tests(open(input_path+"/tests.csv"))
        # Constructing the spectrum
        self._fill_spectrum(open(input_path+"/matrix.txt"))
        return self.sb.get_spectrum()

    @staticmethod
    def check_format(input_path: str) -> bool:
        return (osp.isdir(input_path) and
                osp.isfile(osp.join(input_path, "matrix.txt")) and
                osp.isfile(osp.join(input_path, "spectra.csv")) and
                osp.isfile(osp.join(input_path, "tests.csv")))

    @classmethod
    def write_spectrum(cls, spectrum: Spectrum, directory: str):
        """ Output the spectrum in Gzoltar format """
        type_ = cls.get_type()
        # First check that the directory exists and is empty
        if (not osp.isdir(directory)):
            os.mkdir(directory)
        else:
            rmtree(directory)
            os.mkdir(directory)
        # Next print out the tests
        with open(osp.join(directory, "tests.csv"), 'w') as test_file:
            print("name,outcome,runtime,stacktrace", file=test_file)
            for test in spectrum.tests():
                print(test.name, "PASS" if test.outcome is Outcome.PASSED else
                      "FAIL", "", "", sep=",", file=test_file)
        with open(osp.join(directory, "spectra.csv"), 'w') as units_file:
            print("name", file=units_file)
            # TODO: change _elements below to elements()
            for elem in spectrum._elements:
                print(elem.output_str(type_=type_), file=units_file)
        with open(osp.join(directory, "matrix.txt"), 'w') as matrix_file:
            for test in spectrum.tests():
                for elem in spectrum._elements:
                    print(int(spectrum[test][elem]), end=" ", file=matrix_file)
                print('+' if test.outcome is Outcome.PASS else '-',
                      file=matrix_file)

    @classmethod
    def get_elem_separators(cls):
        return ['$', '#', ':', ':']


if __name__ == "__main__":
    from flitsr.output import print_spectrum
    d = sys.argv[1]
    ginput = Gzoltar()
    spectrum = ginput.read_spectrum(d)
    print_spectrum(spectrum)
