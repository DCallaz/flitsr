import sys
import re
import os
from io import TextIOWrapper
from typing import Dict, Tuple, List
from flitsr.output import print_spectrum
from flitsr.split_faults import split
from flitsr.spectrum import Spectrum, Outcome
from flitsr import errors


def construct_details(f: TextIOWrapper, method_level: bool,
                      spectrum: Spectrum) -> Dict[int, Spectrum.Element]:
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
                    elem = spectrum.addElement(details, faults)
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
                elem = spectrum.addElement(details, faults)
                method_map[i] = elem
            i += 1
    return method_map


def construct_tests(tests_reader: TextIOWrapper, spectrum: Spectrum):
    tests_reader.readline()
    i = 0
    for line in tests_reader:
        m = re.fullmatch('([^,]+),(PASS|FAIL|ERROR)(,.*)?', line.rstrip())
        if (m is None):
            errors.error("incorrectly formatted test line in input file:",
                         line, "terminating...")
        else:
            spectrum.addTest(m.group(1), i, Outcome[m.group(2)])
        i += 1


def fill_spectrum(bin_file: TextIOWrapper, method_map: Dict[int, Spectrum.Element],
                  spectrum: Spectrum):
    for t, test in enumerate(spectrum.tests()):
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
                spectrum.addExecution(test, elem, arr[i] != "0")
                seen.add(elem)
        # Use row to merge equivalences
        spectrum.split_groups_on_test(test)
    # ??? groups.sort(key=lambda group: group[0])
    # Remove groupings from spectrum
    spectrum.remove_unnecessary()


def read_spectrum(input_path: str, split_faults: bool,
                  method_level=False) -> Spectrum:
    spectrum = Spectrum()
    # Getting the details of the elements
    method_map = construct_details(open(input_path+"/spectra.csv"),
                                   method_level, spectrum)
    # Getting the details of the tests
    construct_tests(open(input_path+"/tests.csv"), spectrum)
    # Constructing the spectrum
    fill_spectrum(open(input_path+"/matrix.txt"), method_map, spectrum)
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


if __name__ == "__main__":
    d = sys.argv[1]
    spectrum = read_spectrum(d, False)
    print_spectrum(spectrum)
