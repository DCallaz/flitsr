from typing import List, Dict, Any, Set, Tuple
from flitsr.spectrum import Spectrum, Outcome


class SpectrumBuilder:
    def __init__(self):
        self._elements: List[Spectrum.Element] = []
        self._tests: List[Spectrum.Test] = []
        self._executions: Dict[Spectrum.Test, Set[Spectrum.Element]] = {}

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
        self._executions[t] = set()
        return t

    def addElement(self, details: List[str],
                   faults: List[Any], index: int = None) -> Spectrum.Element:
        """
        Add a new element to the spectrum, with the given details and faults.
        """
        if (index is None):
            index = len(self._elements)
        e = Spectrum.Element(details, index, faults)
        self._elements.append(e)
        return e

    def addExecution(self, test: Spectrum.Test, elem: Spectrum.Element):
        """
        Mark the specified element as executed in the given test.
        """
        if (test not in self._executions):
            self._executions[test] = set()
        self._executions[test].add(elem)

    def addNonExecution(self, test: Spectrum.Test, elem: Spectrum.Element):
        """
        Mark the specified element as not executed in the given test.
        NOTE: Adding non-executions is not required for the spectrum
        (non-execution is assumed by default), thus this method does not do
        anything.
        """
        # if (test not in self._executions):
        #     self._executions[test] = {}
        # self._executions[test][elem] = False
        pass

    def form_groups(self) -> List[Spectrum.Group]:
        """
        Given one test pertaining to a row in the spectrum, split the groups
        according to the coverage. The split will potentially split each group
        in half, based on those elements that are executed in the test, and
        those that are not.
        """
        stack: List[Tuple[Set[Spectrum.Element], int]] = []
        groups: List[Spectrum.Group] = []
        # Initialize stack with all elements in one group
        stack.append((set(self._elements), 0))
        while (len(stack) > 0):
            cur, t_ind = stack.pop()
            if (t_ind >= len(self._tests) or len(cur) == 1):
                groups.append(Spectrum.Group(list(cur)))
            else:
                test = self._tests[t_ind]
                exe_elem = cur.intersection(self._executions[test])
                nexe_elem = cur.difference(exe_elem)
                if (len(exe_elem) != 0):
                    stack.append((exe_elem, t_ind+1))
                if (len(nexe_elem) != 0):
                    stack.append((nexe_elem, t_ind+1))
        return groups

    def get_spectrum(self) -> Spectrum:
        """ Return the computed spectrum """
        groups = self.form_groups()
        spectrum = Spectrum(self._elements, groups, self._tests,
                            self._executions)
        return spectrum


class SpectrumUpdater(SpectrumBuilder):
    def __init__(self, spectrum: Spectrum):
        super().__init__()
        self._elements = spectrum._elements[:]
        self._tests = spectrum.tests()[:]
        self._executions = dict()
        # copy all the executions
        for test in self._tests:
            new_exe = self._executions.setdefault(test, set())
            for group in spectrum.groups():
                # Only copy over actually executed elements
                if (spectrum[test][group]):
                    for elem in group.get_elements():
                        new_exe.add(elem)

    def remove_test_with_executions(self, test: Spectrum.Test):
        self._tests.remove(test)
        del self._executions[test]

    def copy_test_and_execution(self, test: Spectrum.Test, spectrum: Spectrum):
        self._tests.append(test)
        new_exe = self._executions.setdefault(test, set())
        for group in spectrum.groups():
            # Only copy over actually executed elements
            if (spectrum[test][group]):
                for other in group.get_elements():
                    # get this spectrum's element
                    elem = self._get_element(other)
                    new_exe.add(elem)

    def _get_element(self, other: Spectrum.Element):
        for elem in self._elements:
            if (elem.semantic_eq(other)):
                return elem
        raise KeyError(f'Could not find element {other} in SpectrumUpdater')
