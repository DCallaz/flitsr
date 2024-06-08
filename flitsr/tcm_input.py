import sys
import os
from io import TextIOWrapper
from typing import Dict, Tuple
from flitsr.output import find_faults, print_table
from flitsr.split_faults import split
from flitsr.spectrum import Spectrum


def construct_details(f: TextIOWrapper, method_level: bool,
                      spectrum: Spectrum):
    """
    Fills the spectrum object with elements read in from the open file 'f'.
    """
    i = 0  # number of actual lines
    method_map: Dict[int, Spectrum.Element] = {}
    methods: Dict[Tuple[str, str], Spectrum.Element] = {}
    bugs = 0
    line = f.readline()
    while (not line == '\n'):
        l = line.strip().split(' | ')
        faults = []
        if (len(l) > 1):
            if (not l[1].isdigit()):
                faults = [bugs]
            else:
                faults = []
                for b in l[1:]:
                    faults.append(int(b))
            bugs += 1
        if (method_level):
            details = l[0].split(":")
            if (len(details) != 3):
                raise ValueError("Incorrectly formatted line \"" + line +
                                 "\" for method level evaluation")
            if ((details[0], details[1]) not in methods):
                # append with first line number
                elem = spectrum.addElement(details, faults)
                methods[(details[0], details[1])] = elem
                method_map[i] = elem
            else:
                elem = method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
        else:
            details = l[0].split(":")
            elem = spectrum.addElement(details, faults)
            method_map[i] = elem
        i += 1
        line = f.readline()
    return method_map


def construct_tests(f: TextIOWrapper, spectrum: Spectrum):
    line = f.readline()
    while (not line == '\n'):
        row = line.strip().split(" ")
        spectrum.addTest(row[0], row[1] == 'PASSED')
        line = f.readline()


def fill_table(f: TextIOWrapper, method_map: Dict[int, Spectrum.Element],
               spectrum: Spectrum):
    for test in spectrum.tests:
        line = f.readline()
        arr = line.strip().split(' ')
        seen = set()
        for i in range(0, int(len(arr)/2)):
            elem = method_map[int(arr[i*2])]
            if (elem not in seen):
                spectrum.addExecution(test, elem, True)
                seen.add(elem)
        # Use row to merge equivalences
        spectrum.merge_on_test(test)
    # ??? groups.sort(key=lambda group: group[0])
    # Remove groupings from table
    spectrum.remove_unnecessary()


def read_table(input_path: str, split_faults: bool, method_level=False):
    spectrum = Spectrum()
    method_map: Dict[int, Spectrum.Element]
    file = open(input_path)
    while (True):
        line = file.readline()
        if (line == '' or not line.startswith("#")):
            break
        elif (line.startswith("#metadata")):
            while (not line == '\n'):
                line = file.readline()
        elif (line.startswith("#tests")):
            # Constructing the table
            construct_tests(file, spectrum)
        elif (line.startswith("#uuts")):
            # Getting the details of the project
            method_map = construct_details(file, method_level, spectrum)
        elif (line.startswith("#matrix")):
            # Filling the table
            fill_table(file, method_map, spectrum)
    file.close()
    # Split fault groups if necessary
    if (split_faults):
        faults, unexposed = split(find_faults(spectrum), spectrum)
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
    spectrum = read_table(d, False)
    print_table(spectrum)
