import sys
import re
import os
from io import TextIOWrapper
from typing import Dict, Tuple
from flitsr.output import print_spectrum
from flitsr.split_faults import split
from flitsr.spectrum import Spectrum


def construct_details(f: TextIOWrapper, method_level: bool,
                      spectrum: Spectrum) -> Dict[int, Spectrum.Element]:
    """
    Fills the spectrum object with elements read in from the open file 'f'.
    """
    i = 0  # number of actual lines
    method_map: Dict[int, Spectrum.Element] = {}
    methods: Dict[Tuple[str, str], Spectrum.Element] = {}
    bugs = 0
    f.readline()
    for line in f:
        l = line.strip().split(':')
        r = re.search("(.*)\\$(.*)#([^:]*)", l[0])
        if (r is None):
            raise ValueError("Incorrectly formatted line \"" + line +
                             "\" when reading input file")
        faults = []
        if (len(l) > 2):
            if (not l[2].isdigit()):
                faults = [bugs]
            else:
                faults = []
                for b in l[2:]:
                    faults.append(int(b))
            bugs += 1
        if (method_level):
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            if ((details[0], details[1]) not in methods):
                # add with first line number
                elem = spectrum.addElement(details, faults)
                methods[(details[0], details[1])] = elem
                method_map[i] = elem
            else:
                elem = method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
        else:
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            elem = spectrum.addElement(details, faults)
            method_map[i] = elem
        i += 1
    return method_map


def construct_tests(tests_reader: TextIOWrapper, spectrum: Spectrum):
    tests_reader.readline()
    for r in tests_reader:
        row = r.strip().split(",")
        spectrum.addTest(row[0], row[1] == 'PASS')


def fill_spectrum(bin_file: TextIOWrapper, method_map: Dict[int, Spectrum.Element],
                  spectrum: Spectrum):
    for test in spectrum.tests:
        line = bin_file.readline()
        arr = line.strip().split()
        seen = set()
        # Loop over all elements in test exec (remove test outcome at the end)
        for i in range(0, len(arr)-1):
            elem = method_map[i]
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
        for elem in spectrum.elements:
            if (elem in unexposed):
                elem.faults = []
                print("Dropped faulty UUT:", elem, "due to unexposure")
            fault_items = []
            for item in faults.items():
                if (elem in item[1]):
                    fault_items.append(item[0])
            if (len(fault_items) != 0):
                elem.faults = fault_items
        if (len(faults) == 0):
            print("No exposable faults in", input_path)
            quit()
    return spectrum


if __name__ == "__main__":
    d = sys.argv[1]
    spectrum = read_spectrum(d, False)
    print_spectrum(spectrum)
