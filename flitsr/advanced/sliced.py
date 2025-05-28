import re
from flitsr.advanced.attributes import existing
from flitsr.advanced.refiner import Refiner
from flitsr.spectrum import Spectrum, Outcome
from flitsr.spectrumBuilder import SpectrumUpdater
from flitsr.input import read_spectrum


class Sliced(Refiner):
    @existing('method', 'split')
    def __init__(self, unclustered_input: str, split: bool, method: bool):
        self.old_spectrum = read_spectrum(unclustered_input, split, method)

    def find_old_test(self, sliced_test: Spectrum.Test):
        """ Search for old test """
        search_name = self.get_name(sliced_test)
        for t in self.old_spectrum.tests():
            if (t.name == search_name):
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

    def refine(self, spectrum: Spectrum, method_lvl=False) -> Spectrum:
        print("Refining spectrum!")
        sb = SpectrumUpdater(spectrum)
        for failed in spectrum.failing():
            old_test = self.find_old_test(failed)
            if (old_test is not None and old_test.outcome is Outcome.PASS):
                print(failed, "is not failing in original")
                sb.remove_test_with_executions(failed)
                sb.copy_test_and_execution(old_test,
                                           self.old_spectrum[old_test])
        print("Finished refining!")
        return sb.get_spectrum()
