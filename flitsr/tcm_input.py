import sys
import os
from io import TextIOWrapper
from typing import Dict, Tuple, List
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
    i = 0
    while (not line == '\n'):
        row = line.strip().split(" ")
        spectrum.addTest(row[0], i, row[1] == 'PASSED')
        line = f.readline()
        i += 1


def fill_spectrum(f: TextIOWrapper, method_map: Dict[int, Spectrum.Element],
               spectrum: Spectrum):
    for test in spectrum.tests():
        line = f.readline()
        arr = line.strip().split(' ')
        seen = set()
        for i in range(0, int(len(arr)/2)):
            elem = method_map[int(arr[i*2])]
            if (elem not in seen):
                spectrum.addExecution(test, elem, True)
                seen.add(elem)
        # Use row to merge equivalences
        spectrum.split_groups_on_test(test)
    # ??? groups.sort(key=lambda group: group[0])
    # Remove groupings from spectrum
    spectrum.remove_unnecessary()


def read_spectrum(input_path: str, split_faults: bool,
                  method_level=False) -> Spectrum:
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
            # Constructing the spectrum
            construct_tests(file, spectrum)
        elif (line.startswith("#uuts")):
            # Getting the details of the project
            method_map = construct_details(file, method_level, spectrum)
        elif (line.startswith("#matrix")):
            # Filling the spectrum
            fill_spectrum(file, method_map, spectrum)
    file.close()
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
            print("No exposable faults in", input_path, file=sys.stderr)
            quit()
    return spectrum


if __name__ == "__main__":
    d = sys.argv[1]
    spectrum = read_spectrum(d, False)
    print_spectrum(spectrum)
