import sys
import re
import os
from os import path as osp
from io import TextIOWrapper
from shutil import rmtree
from typing import Dict, Tuple, List
from flitsr.split_faults import split
from flitsr.spectrum import Spectrum, Outcome
from flitsr.spectrumBuilder import SpectrumBuilder
from flitsr import errors
from flitsr.input.input_reader import Input


class Gzoltar(Input):
    def get_run_file_name(self, input_path: str):
        return input_path.split("/")[0] + ".run"

    def construct_details(self, f: TextIOWrapper, method_level: bool,
                          sb: SpectrumBuilder) -> Dict[int, Spectrum.Element]:
        """
        Fills the spectrum object with elements read in from the open file 'f'.
        """
        i = 0  # number of actual lines
        method_map: Dict[int, Spectrum.Element] = {}
        methods: Dict[Tuple[str, str], Spectrum.Element] = {}
        bugs = 0
        assert f.readline() == 'name\n'  # remove header
        for line in f:
            m = re.fullmatch('([^$]+)\\$([^#]+)#([^:]+):([0-9]+)(?::(.+))?',
                             line.rstrip())
            if (m is None):
                errors.error("Incorrectly formatted line \"" + line +
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
                if (method_level):
                    details = [m.group(1)+"."+m.group(2), m.group(3), m.group(4)]
                    if ((details[0], details[1]) not in methods):
                        # add with first line number
                        elem = sb.addElement(details, faults)
                        methods[(details[0], details[1])] = elem
                        method_map[i] = elem
                    else:
                        elem = method_map[i] = methods[(details[0], details[1])]
                        # update method's faults
                        for fault in faults:
                            if (fault not in elem.faults):
                                elem.faults.append(fault)
                else:
                    details = [m.group(1)+"."+m.group(2), m.group(3), m.group(4)]
                    elem = sb.addElement(details, faults)
                    method_map[i] = elem
                i += 1
        return method_map

    def construct_tests(self, tests_reader: TextIOWrapper, sb: SpectrumBuilder):
        tests_reader.readline()
        i = 0
        for line in tests_reader:
            m = re.fullmatch('([^,]+),(PASS|FAIL|ERROR)(,.*)?', line.rstrip())
            if (m is None):
                errors.error("incorrectly formatted test line in input file:",
                             line, "terminating...")
            else:
                sb.addTest(m.group(1), i, Outcome[m.group(2)])
            i += 1

    def fill_spectrum(self, bin_file: TextIOWrapper,
                      method_map: Dict[int, Spectrum.Element],
                      sb: SpectrumBuilder):
        for t, test in enumerate(sb.get_tests()):
            line = bin_file.readline()
            if (line == ''):
                errors.error('Incorrect number of matrix lines', f'({t})',
                             'in input file, terminating...')
            arr = line.rstrip().split()
            seen = set()
            # Loop over all elements in test exec (remove test outcome at the end)
            for i in range(0, len(arr)-1):
                try:
                    elem = method_map[i]
                except KeyError:
                    errors.error('Incorrect number of matrix columns', f'({i})',
                                 'in input file, terminating...')
                if (arr[i] != "0" and elem not in seen):
                    sb.addExecution(test, elem)
                    seen.add(elem)

    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        sb = SpectrumBuilder()
        # Getting the details of the elements
        method_map = self.construct_details(open(input_path+"/spectra.csv"),
                                            method_level, sb)
        # Getting the details of the tests
        self.construct_tests(open(input_path+"/tests.csv"), sb)
        # Constructing the spectrum
        self.fill_spectrum(open(input_path+"/matrix.txt"), method_map, sb)
        spectrum = sb.get_spectrum()
        del sb
        # Split fault groups if necessary
        if (split_faults):
            faults, unexposed = split(spectrum.get_faults(), spectrum)
            for elem in unexposed:
                elem.faults.clear()
                print("WARNING: Dropped faulty UUT:", elem, "due to unexposure",
                      file=sys.stderr)
            # Get element's fault lists
            fault_lists: Dict[Spectrum.Element, List[float]] = {}
            for (f_num, f_locs) in faults.items():
                for elem in f_locs:
                    fault_lists.setdefault(elem, []).append(f_num)
            # Set element's fault lists
            for (elem, f_list) in fault_lists.items():
                elem.faults = f_list
            if (len(faults) == 0):
                print("ERROR: No exposable faults in ", input_path, ", terminating...",
                        sep="", file=sys.stderr)
                quit()
        return spectrum

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
    spectrum = ginput.read_spectrum(d, False)
    print_spectrum(spectrum)
