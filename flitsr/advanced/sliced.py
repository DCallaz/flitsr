import re
from os import path as osp
from flitsr.advanced.attributes import existing
from flitsr.advanced.refiner import Refiner
from flitsr.spectrum import Spectrum, Outcome
from flitsr.spectrumBuilder import SpectrumUpdater
from flitsr.input import read_spectrum


class Sliced(Refiner):
    @existing('method', 'split', 'input')
    def __init__(self, unsliced_spectrum: str, split: bool, method: bool,
                 input: str):
        abs_input = osp.abspath(input)
        pth = osp.dirname(abs_input)
        bsnm, ext = osp.splitext(osp.basename(abs_input))
        conv_spectrum = unsliced_spectrum.format(pth=pth, bsnm=bsnm, ext=ext)
        self.unsliced_spectrum = read_spectrum(conv_spectrum, split, method)

    def find_test(self, spectrum, test_name: 'str'):
        """ Search for a test with the given name in the given spectrum """
        for t in spectrum.tests():
            if (t.name == test_name):
                return t
        return None

    def get_name(self, sliced_test: Spectrum.Test):
        """ Get the un-sliced name of the given test """
        sliced_name = sliced_test.name
        match = re.fullmatch('(.+#\\w+)_\\d+', sliced_name)
        if (match is None):
            search_name = sliced_name
        else:
            search_name = match.group(1)
        return search_name

    def refine(self, sliced_spectrum: Spectrum, method_lvl=False) -> Spectrum:
        # print("Refining spectrum!")
        sb = SpectrumUpdater(sliced_spectrum)
        for failed in sliced_spectrum.failing():
            name = self.get_name(failed)
            old_test = self.find_test(self.unsliced_spectrum, name)
            if (old_test is not None and old_test.outcome is Outcome.PASS):
                # print(failed, "is not failing in original")
                sb.remove_test_with_executions(failed)
                sb.copy_test_and_execution(old_test,
                                           self.unsliced_spectrum[old_test])
        # print("Finished refining!")
        return sb.get_spectrum()
