import sys
from flitsr.spectrum import Spectrum
from typing import Dict, List, Set, Tuple, Any
from flitsr.input.input_reader import Input
from flitsr.errors import warning


class NoFaultsError(ValueError):
    """
    Exception class for when splitting the fauls causes there to be no
    exposable faults left in the spectrum
    """
    pass


def split_spectrum_faults(spectrum: Spectrum):
    """
    Splits fault groups that are a combination of two or more sub-faults in
    mutually exclusive parts of the system into separate faults, as well as
    removing faults that are not exposed. Operates on the spectrum in-place.

    Raises:
        NoFaultsError: When there are no exposed faults in the spectrum after
            splitting. Note that the spectrum is still modified when this is
            thrown, so this can be ignored in the client code.
    """
    faults, unexposed = split(spectrum)
    for elem in unexposed:
        elem.faults.clear()
        warning(f"Dropped faulty UUT: {elem} due to unexposure")
    # Get element's fault lists
    fault_lists: Dict[Spectrum.Element, List[float]] = {}
    for (f_num, f_locs) in faults.items():
        for elem in f_locs:
            fault_lists.setdefault(elem, []).append(f_num)
    # Set element's fault lists
    for (elem, f_list) in fault_lists.items():
        elem.faults = f_list
    if (len(faults) == 0):
        raise NoFaultsError()


def split(spectrum: Spectrum) -> Tuple[Dict[float, Set[Spectrum.Element]],
                                       Set[Spectrum.Element]]:
    """
    Splits fault groups that are a combination of two or more sub-faults in
    mutually exclusive parts of the system into separate faults. Also finds
    faults that are not exposed and returns them separately.
    """
    faults = spectrum.get_faults()
    if (faults == {}):
        return {}, set()
    ftemp = [(set(elem), f[0], False) for f in faults.items() for elem in f[1]]
    for test in spectrum.failing():
        merge: Dict[Any, Set[Spectrum.Element]] = {}
        remain = []
        for equiv in ftemp:
            if (any(spectrum[test][e] for e in equiv[0])):
                merge.setdefault(equiv[1], set()).update(equiv[0])
            else:
                remain.append(equiv)
        if (len(merge) != 0):
            for (f_num, f_locs) in merge.items():
                remain.append((f_locs, f_num, True))
        ftemp = remain
    fmap: Dict[float, List[Set[Spectrum.Element]]] = {}
    unexposed: Set[Spectrum.Element] = set()
    for equiv in ftemp:
        if (not equiv[2]):
            unexposed.update(equiv[0])
            continue
        fmap.setdefault(equiv[1], []).append(equiv[0])
    new_faults: Dict[float, Set[Spectrum.Element]] = {}
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
    num_only = False
    while (True):
        if (len(sys.argv) > i):
            if (sys.argv[i] == "num"):
                num_only = True
            else:
                print("Unknown option:", sys.argv[i])
                quit()
            i += 1
        else:
            break
    spectrum = Input.read_in(d, False)
    faults = spectrum.get_faults()
    print("faults:", faults)
    # print(groups)
    # print_spectrum(spectrum)
    faults, unexposed = split(spectrum)
    print("split faults:", faults)
    print("unexposed:", unexposed)
