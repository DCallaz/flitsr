import sys
import re
import os
from flitsr.output import find_faults, print_table
from flitsr.split_faults import split
from flitsr.spectrum import Spectrum


def construct_details(f, method_level, spectrum):
    """
    Constructs a details object containing the information related to each
    element of the form:
    [
        (<location tuple>, [<fault_num>,...] or <fault_num> or -1),
        ...
    ]
    """
    i = 0  # number of actual lines
    method_map = {}
    methods = {}
    bugs = 0
    f.readline()
    for line in f:
        l = line.strip().split(':')
        r = re.search("(.*)\$(.*)#([^:]*)", l[0])
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


def construct_tests(tests_reader, spectrum):
    num_tests = 0
    tests_reader.readline()
    for r in tests_reader:
        row = r.strip().split(",")
        spectrum.addTest(row[0], row[1] == 'PASS')
        num_tests += 1
    return num_tests


def fill_table(num_tests, bin_file, method_map, spectrum):
    for test in spectrum.tests:
        line = bin_file.readline()
        arr = line.strip().split()
        seen = []
        for i in range(0, len(arr)-1):
            elem = method_map[i]
            spectrum.addExecution(test, elem, arr[i] != "0")
            if (arr[i] != "0" and elem not in seen):
                seen.append(elem)
                if (test.outcome):
                    spectrum.p[elem] += 1
                else:
                    spectrum.f[elem] += 1
        # Use row to merge equivalences
        spectrum.merge_on_test(test)
        # Increment total counts, and append row to table
        if (test.outcome):
            spectrum.tp += 1
        else:
            spectrum.tf += 1
    # ??? groups.sort(key=lambda group: group[0])
    # Remove groupings from table
    spectrum.remove_unnecessary()


def read_table(directory, split_faults, method_level=False):
    spectrum = Spectrum()
    # Getting the details of the elements
    method_map = construct_details(open(directory+"/spectra.csv"),
                                   method_level, spectrum)
    # Getting the details of the tests
    num_tests = construct_tests(open(directory+"/tests.csv"), spectrum)
    # Constructing the table
    fill_table(num_tests, open(directory+"/matrix.txt"), method_map, spectrum)
    # Split fault groups if necessary
    if (split_faults):
        faults, unexposed = split(find_faults(spectrum), spectrum)
        for elem in spectrum.elements:
            if (elem in unexposed):
                elem.faults = []
                print("Dropped faulty UUT:", elem.details, "due to unexposure")
            fault_items = []
            for item in faults.items():
                if (elem in item[1]):
                    fault_items.append(item[0])
            if (len(fault_items) != 0):
                elem.faults = fault_items
        if (len(faults) == 0):
            print("No exposable faults in", directory)
            quit()
    return spectrum


if __name__ == "__main__":
    d = sys.argv[1]
    spectrum = read_table(d, False)
    print_table(spectrum)
