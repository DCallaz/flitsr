import sys
from os import path as osp
from io import TextIOWrapper
import re
import mmap
from flitsr.spectrum import Spectrum, Outcome
from flitsr.spectrumBuilder import SpectrumBuilder, TestKeyError, ElemKeyError
from flitsr.errors import error
from flitsr.input.input_reader import Input
from flitsr.split_faults import split_spectrum_faults, NoFaultsError


class TCM(Input):
    def get_run_file_name(self, input_path: str):
        return re.sub("\\.\\w+$", ".run", input_path)

    def construct_details(self, f: TextIOWrapper, method_level: bool,
                          sb: SpectrumBuilder):
        """
        Fills the spectrum object with elements read in from the open file 'f'.
        """
        bugs = 0
        line = f.readline()
        while (not line == '\n'):
            m = re.fullmatch('((?:[^ ]| [^|])+)(?: \\| (.+))?', line.rstrip())
            if (m is None):
                error("incorrectly formatted element line in input file:",
                      line, "terminating...")
            else:
                faults = []
                if (m.group(2) is not None):
                    bs = m.group(2).split(' | ')
                    if (not bs[0].isdigit()):
                        faults = [bugs]
                    else:
                        faults = []
                        for b in bs:
                            faults.append(int(b))
                    bugs += 1
                if (method_level):
                    details_m = re.match('([^:]+):([^:]+):([0-9]+)',
                                         m.group(1))
                    if (details_m is None):
                        error("Incorrectly formatted line \"" + line +
                              "\" for method level evaluation")
                    else:
                        details = list(details_m.groups())
                else:
                    details = m.group(1).split(":")
                sb.addElement(details, faults)
                line = f.readline()

    def construct_tests(self, f: TextIOWrapper, sb: SpectrumBuilder):
        line = f.readline()
        while (not line == '\n'):
            m = re.fullmatch('([^ ]+) (PASSED|FAILED|ERROR)( .*)?',
                             line.rstrip())
            if (m is None):
                error("incorrectly formatted test line in input file:", line,
                      "terminating...")
            else:
                sb.addTest(m.group(1), Outcome[m.group(2)])
            line = f.readline()

    def fill_spectrum(self, f: TextIOWrapper, sb: SpectrumBuilder):
        for t, test in enumerate(sb.get_tests()):
            line = f.readline()
            if (line == ''):
                error('Incorrect number of matrix lines', f'({t})',
                      'in input file, terminating...')
            arr = line.rstrip().split()
            for i in range(0, len(arr), 2):
                try:
                    sb.addExecution(t, int(arr[i]))
                except ElemKeyError:
                    error(f'Incorrect element reference "{arr[i]}"',
                          f'at column {i*2+1} on line {t} of the matrix',
                          'component in the input file, terminating...')
                except TestKeyError:
                    error('Incorrect number of matrix lines', f'({t})',
                          'in input file, terminating...')

    def read_spectrum(self, input_path: str, split_faults: bool,
                      method_level=False) -> Spectrum:
        sb = SpectrumBuilder(method_level)
        file = open(input_path)
        exec_checks = {'#tests': False, '#uuts': False, '#matrix': False}
        while (True):
            line = file.readline()
            if (line == '' or not line.startswith("#")):
                break
            elif (line.startswith("#metadata")):
                while (not line == '\n'):
                    line = file.readline()
            elif (line.startswith("#tests")):
                if (exec_checks['#tests'] is True):
                    print("WARNING: duplicate #tests component in input file",
                          file=sys.stderr)
                # Constructing the spectrum
                self.construct_tests(file, sb)
                exec_checks['#tests'] = True
            elif (line.startswith("#uuts")):
                if (exec_checks['#uuts'] is True):
                    print("WARNING: duplicate #uuts component in input file",
                          file=sys.stderr)
                # Getting the details of the project
                self.construct_details(file, method_level, sb)
                exec_checks['#uuts'] = True
            elif (line.startswith("#matrix")):
                if (exec_checks['#matrix'] is True):
                    print("WARNING: duplicate #matrix component in input file",
                          file=sys.stderr)
                # Filling the spectrum
                self.fill_spectrum(file, sb)
                exec_checks['#matrix'] = True
            else:
                print("ERROR: Incorrectly formatted input file at line:", line,
                      "terminating...", file=sys.stderr)
                quit()
        file.close()
        if (sum(exec_checks.values()) != 3):
            missing = [e[0] for e in exec_checks.items() if e[1] is False]
            error(f"Input file missing components: {missing}, terminating...")
        spectrum = sb.get_spectrum()
        del sb
        # Split fault groups if necessary
        if (split_faults):
            try:
                split_spectrum_faults(spectrum)
            except NoFaultsError:
                error(f"No exposable faults in {input_path}, terminating...")
        return spectrum

    @staticmethod
    def check_format(input_path: str) -> bool:
        if (osp.isfile(input_path)):
            with open(input_path, 'rb', 0) as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as f:
                    return f.find(b'#uuts') != -1 and f.find(b'#tests') != -1 \
                        and f.find(b'#matrix') != -1
        return False

    @classmethod
    def write_spectrum(cls, spectrum: Spectrum, output_path: str):
        """ Output the spectrum in TCM format """
        with open(output_path, 'w') as file:
            type_ = cls.get_type()
            print("#tests", file=file)
            for test in spectrum.tests():
                print(test.name, test.outcome.name, file=file)
            print(file=file)
            print("#uuts", file=file)
            # TODO: change _elements below to elements()
            for elem in spectrum._elements:
                print(elem.output_str(type_=type_), file=file)
            print(file=file)
            print("#matrix", file=file)
            for test in spectrum.tests():
                first = True
                for elem_id, elem in enumerate(spectrum._elements):
                    if (spectrum[test][elem]):
                        print(("" if first else " ")+str(elem_id), "1", end="",
                              file=file)
                        first = False
                print(file=file)

    @classmethod
    def get_elem_separators(cls):
        return ['.', ':', ':', ' | ']


if __name__ == "__main__":
    from flitsr.output import print_spectrum
    d = sys.argv[1]
    tinput = TCM()
    spectrum = tinput.read_spectrum(d, False)
    print_spectrum(spectrum)
