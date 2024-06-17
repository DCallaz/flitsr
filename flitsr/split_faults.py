import sys
from flitsr.spectrum import Spectrum
from flitsr.output import find_fault_groups, find_faults
from typing import Dict, List


def getMapping(faults: Dict[int, List[Spectrum.Element]],
               spectrum: Spectrum) -> Dict[Spectrum.Element, int]:
    faults_comb = [e for l in faults.values() for e in l]
    mapping: Dict[Spectrum.Element, int] = {}
    for elem in faults_comb:
        for i in range(len(spectrum.groups)):
            if elem in spectrum.groups[i]:
                mapping[elem] = i
    return mapping


def bit(test: Spectrum.Test, equiv: List[Spectrum.Element],
        mapping: Dict[Spectrum.Element, int], spectrum: Spectrum) -> bool:
    b = False
    for fault in equiv:
        b = b or spectrum[test][mapping[fault]]
    return b


def split(faults: Dict[int, List[Spectrum.Element]], spectrum: Spectrum):
    mapping = getMapping(faults, spectrum)
    if (faults == {}):
        return {}, []
    ftemp = [([elem], f[0], False) for f in faults.items() for elem in f[1]]
    # print("Failures before", failures)
    for test in spectrum:
        merge: Dict[int, List[Spectrum.Element]] = {}
        remain = []
        for equiv in ftemp:
            if (bit(test, equiv[0], mapping, spectrum)):
                if (equiv[1] not in merge):
                    merge[equiv[1]] = []
                merge[equiv[1]] += equiv[0]
            else:
                remain.append(equiv)
        if (len(merge) != 0):
            for item in merge.items():
                remain.append((item[1], item[0], True))
        ftemp = remain
    # print(ftemp)
    fmap: Dict[float, List[List[Spectrum.Element]]] = {}
    unexposed = []
    for equiv in ftemp:
        if (not equiv[2]):
            unexposed.extend(equiv[0])
            continue
        fmap.setdefault(equiv[1], []).append(equiv[0])
    new_faults = {}
    for item2 in fmap.items():
        if (len(item2[1]) == 1):
            new_faults[item2[0]] = item2[1][0]
        else:
            for i in range(len(item2[1])):
                new_faults[float("{}.{}".format(item2[0], i+1))] = item2[1][i]
    return new_faults, unexposed


if __name__ == "__main__":
    d = sys.argv[1]
    i = 2
    gzoltar = False
    num_only = False
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "gzoltar"):
                gzoltar = True
            elif (sys.argv[i] == "num"):
                num_only = True
            else:
                print("Unknown option:", sys.argv[i])
                quit()
            i += 1
        else:
            break
    if (gzoltar):
        from flitsr.input import read_spectrum
    else:
        from flitsr.tcm_input import read_spectrum
    spectrum = read_spectrum(d, False)
    faults = find_faults(spectrum)
    print("faults:", faults)
    #print(groups)
    #print_spectrum(spectrum)
    faults, unexposed = split(faults, spectrum)
    print("split faults:", faults)
    print("unexposed:", unexposed)
