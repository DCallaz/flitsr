import subprocess
import re
from flitsr.suspicious import Suspicious
from flitsr.spectrum import Spectrum
import copy
import os
from typing import List


def parallel(d: str, spectrum: Spectrum, parType: str) -> List[Spectrum]:
    spectrums = partition_table(d, spectrum, parType)
    return spectrums


def partition_table(d: str, spectrum: Spectrum,
                    parType: str) -> List[Spectrum]:
    jar_file = os.path.join(os.environ['FLITSR_HOME'], 'flitsr',
                            'parallel-1.0-SNAPSHOT-jar-with-dependencies.jar')
    output = subprocess.check_output(['java', '-jar', jar_file, d,
                                      parType]).decode('utf-8')
    partitions = re.split("partition \\d+\n", output)[1:]
    spectrums: List[Spectrum] = []
    for partition in partitions:
        new_spectrum = copy.deepcopy(spectrum)
        tests = [int(i) for i in partition.strip().split("\n")]
        toRemove = set()
        # keep failing + all passing
        for test in new_spectrum.failing():
            if (test.index not in tests):
                toRemove.add(test)
        for test in toRemove:
            new_spectrum.remove(test, hard=True)
        trim_elements(new_spectrum)
        spectrums.append(new_spectrum)
    return spectrums


def trim_elements(spectrum):
    """Remove elements that are not in this block (i.e. ef = 0)"""
    toRemove = set()
    for elem in spectrum.elements():
        if (spectrum.f[elem] == 0):
            toRemove.add(elem)
    for elem in toRemove:
        spectrum.remove_element(elem)
