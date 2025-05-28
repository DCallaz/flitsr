from typing import List, Dict, Any
from flitsr.spectrum import Spectrum, Outcome


class SpectrumBuilder:
    def __init__(self):
        self._elements: List[Spectrum.Element] = []
        self._tests: List[Spectrum.Test] = []
        self._groups: List[Spectrum.Group] = [Spectrum.Group()]
        self._executions: Dict[Spectrum.Test, Dict[Spectrum.Element, bool]] = {}

    def get_tests(self):
        return self._tests

    def addTest(self, name: str, index: int, outcome: Outcome):
        """
        Add a new test to the spectrum with the given name, index, and outcome.

        :param name: the name of the test
        :param index: a unique identifier for this test (this may be modified)
        :param outcome: the outcome (pass/fail) of the test
        """
        t = Spectrum.Test(name, index, outcome)
        self._tests.append(t)
        self._executions[t] = {}
        return t

    def addElement(self, details: List[str],
                   faults: List[Any]) -> Spectrum.Element:
        """
        Add a new element to the spectrum, with the given details and faults.
        """
        e = Spectrum.Element(details, len(self._elements), faults)
        self._elements.append(e)
        self._groups[0].append(e)
        return e

    def addExecution(self, test: Spectrum.Test, elem: Spectrum.Element):
        """
        Mark the specified element as executed in the given test.
        """
        if (test not in self._executions):
            self._executions[test] = {}
        self._executions[test][elem] = True

    def addNonExecution(self, test: Spectrum.Test, elem: Spectrum.Element):
        """
        Mark the specified element as not executed in the given test.
        NOTE: Adding non-executions is not required for the spectrum
        (non-execution is assumed by default), and may consume large amounts
        of memory due to the size of the spectrum. Therefore it is advised to
        call this method with cation.
        """
        if (test not in self._executions):
            self._executions[test] = {}
        self._executions[test][elem] = False

    def split_groups_on_test(self, test: Spectrum.Test):
        """
        Given one test pertaining to a row in the spectrum, split the groups
        according to the coverage. The split will potentially split each group
        in half, based on those elements that are executed in the test, and
        those that are not.
        """
        row = self._executions[test]
        new_groups: List[Spectrum.Group] = []
        for group in self._groups:
            elems = group.get_elements()
            collect: List[List[Spectrum.Element]] = [[], []]
            for elem in elems:
                collect[row.get(elem, False)].append(elem)
            for c in collect:
                if (c != []):
                    new_groups.append(Spectrum.Group(c))
        self._groups = new_groups

    def get_spectrum(self):
        """ Return the computed spectrum """
        spectrum = Spectrum(self._elements, self._groups, self._tests,
                            self._executions)
        return spectrum


class SpectrumUpdater(SpectrumBuilder):
    def __init__(self, spectrum: Spectrum):
        super().__init__()
        self._elements = spectrum._elements[:]
        self._tests = spectrum.tests()[:]
        self._groups = spectrum.groups()[:]
        self._executions = dict()
        for test in self._tests:
            self._copy_execution(test, spectrum[test])

    def remove_test_with_executions(self, test: Spectrum.Test):
        self._tests.remove(test)
        del self._executions[test]

    def copy_test_and_execution(self, test: Spectrum.Test,
                                exe: Spectrum.Execution):
        self._tests.append(test)
        self._copy_execution(test, exe)

    def _copy_execution(self, test: Spectrum.Test, exe: Spectrum.Execution):
        new_exe = self._executions.setdefault(test, dict())
        for group in self._groups:
            executed = exe[group]
            # Only copy over actually executed elements
            if (executed):
                for elem in group.get_elements():
                    new_exe[elem] = executed
