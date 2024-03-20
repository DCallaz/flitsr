import sys
from spectrum import Spectrum
from typing import Dict, List


def find_groups(faulties, spectrum):
    ret = []
    for faulty in faulties:
        group = []
        for elem in spectrum.groups[faulty]:
            group.append((details[elem], elem))
        ret.append(group)
    return ret


def print_names(details, faulty, groups, scores=None, file=sys.stdout):
    names = find_names(details, faulty, groups)
    i = 0
    for group in names:
        if (scores == None):
            print("Faulty grouping ("+str(faulty[i])+"): ","[", file=file)
        else:
            print("Faulty grouping ("+str(faulty[i])+"):", scores[i][0],"[",
                    file=file)
        i += 1
        for name in group:
            #arr[0] = os.path.join(*arr[0].split('.'))
            print("  ("+str(name[1])+")", "|".join(name[0][0]),
                "(FAULT {})".format(",".join(str(x) for x in name[0][1]))
                    if (name[0][1]) else "", file=file)
        print("]", file=file)


def print_table(spectrum):
    for test in spectrum:
        row = spectrum[test]
        i = 0
        p = False
        for elem in row:
            col = row[elem]
            if (i == 1):
                p = col
            elif (i > 1):
                print(float(col), end=" ")
            i += 1
        if (p):
            print('+')
        else:
            print('-')


def find_faults(spectrum: Spectrum) -> Dict[int, List[Spectrum.Element]]:
    actual_faults: Dict[int, List[Spectrum.Element]] = dict()
    for elem in spectrum.elements:
        if (elem.faults):
            for fault in elem.faults:
                if (fault not in actual_faults):
                    actual_faults[fault] = []
                actual_faults[fault].append(elem)
    return actual_faults


def find_fault_groups(spectrum: Spectrum):
    faults = find_faults(spectrum)
    fault_groups = {}
    for i in range(len(spectrum.groups)):
        for item in faults.items():
            fault_num = item[0]
            for elem in item[1]:
                if (elem in spectrum.groups[i]):
                    if (fault_num not in fault_groups):
                        fault_groups[fault_num] = set()
                    fault_groups[fault_num].add(i)
                    break
    return fault_groups
