import subprocess
import re
import copy
import os
from typing import List
import tempfile
from importlib import resources
from flitsr.spectrum import Spectrum
from flitsr.advanced.cluster import Cluster
from flitsr.advanced.attributes import choices
from flitsr.input import InputType


class Parallel(Cluster):
    """
    Run one of the parallel debugging algorithms on the spectrum to
    produce multiple spectrums, and process all other options on
    each spectrum.
    """

    @choices('parType', ['bdm', 'msp', 'hwk', 'vwk'])
    def __init__(self, parType: str = 'msp'):
        self.parType = parType

    def cluster(self, inp_file: str, spectrum: Spectrum,
                method_lvl=False) -> List[Spectrum]:
        # write the spectrum to a temporary file
        tmp_fd, tmp_name = tempfile.mkstemp(text=True)
        inp_file = tmp_name
        InputType['TCM'].value.write_spectrum(spectrum, tmp_name)
        # Run the parallel algorithm
        spectrums = self.partition_table(inp_file, spectrum)
        # remove temporary file
        os.remove(tmp_name)
        return spectrums

    def partition_table(self, d: str, spectrum: Spectrum) -> List[Spectrum]:
        jar_name = 'parallel-1.0-SNAPSHOT-jar-with-dependencies.jar'
        with resources.path('flitsr.advanced', jar_name) as jar_file:
            output = subprocess.check_output(['java', '-jar', str(jar_file), d,
                                              self.parType]).decode('utf-8')
        partitions = re.split("partition \\d+\n", output)[1:]
        spectrums: List[Spectrum] = []
        for partition in partitions:
            new_spectrum = copy.deepcopy(spectrum)
            tests = [int(i) for i in partition.strip().split("\n")]
            toRemove = set()
            all_tests = spectrum.tests()
            # keep failing + all passing
            for test in spectrum.failing():
                ind = all_tests.index(test)
                if (ind not in tests):
                    toRemove.add(test)
            for test in toRemove:
                new_spectrum.remove(test, hard=True)
            self.trim_groups(new_spectrum)
            spectrums.append(new_spectrum)
        return spectrums

    def trim_groups(self, spectrum):
        """Remove groups that are not in this block (i.e. ef = 0)"""
        toRemove = set()
        for group in spectrum.groups():
            if (spectrum.f[group] == 0):
                toRemove.add(group)
        for group in toRemove:
            spectrum.remove_group(group)
