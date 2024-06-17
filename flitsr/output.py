import sys
from typing import Dict, List, Set
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


def find_group(elem: Spectrum.Element,
               spectrum: Spectrum) -> List[Spectrum.Element]:
    for group in spectrum.groups:
        if (elem in group):
            return group
    raise KeyError("Element \""+str(elem)+"\" not found in a spectrum group")


def print_names(spectrum, scores=None, file=sys.stdout):
    no_scores = False
    if (scores is None):  # make a tempoorary Scores object
        scores = Scores()
        for elem in spectrum.elements:
            scores.append(elem, 0, 0)
        no_scores = True
    for score in scores:
        if (no_scores):
            print("Faulty grouping: ", "[", file=file)
        else:
            print("Faulty grouping:", score.score, "[", file=file)
        group = find_group(score.elem, spectrum)
        for elem in group:
            print(" ", elem, file=file)
        print("]", file=file)


# TODO: this function does not produce nice looking output
def print_spectrum(spectrum: Spectrum):
    for test in spectrum:
        print(test.name, end=": ")
        row = spectrum[test]
        for elem in row:
            if (row[elem]):
                print(elem, end=" ")
        if (test.outcome):
            print('+')
        else:
            print('-')


def print_csv(spectrum: Spectrum, scores: Scores, file=sys.stdout):
    print("name;suspiciousness_value", file=file)
    for score in scores:
        group = find_group(score.elem, spectrum)
        for elem in group:
            path_part = elem.path.rpartition('.')
            print(elem.gzoltar_str(), ';', score.score, sep='', file=file)


def find_faults(spectrum: Spectrum) -> Dict[int, List[Spectrum.Element]]:
    actual_faults: Dict[int, List[Spectrum.Element]] = dict()
    for group in spectrum.groups:
        for elem in group:
            if (elem.faults):
                for fault in elem.faults:
                    if (fault not in actual_faults):
                        actual_faults[fault] = []
                    actual_faults[fault].append(elem)
    return actual_faults


def find_fault_groups(spectrum: Spectrum) -> Dict[int, Set[int]]:
    faults = find_faults(spectrum)
    fault_groups: Dict[int, Set[int]] = {}
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
