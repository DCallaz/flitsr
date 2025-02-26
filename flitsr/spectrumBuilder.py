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
        t = Spectrum.Test(name, index, outcome)
        self._tests.append(t)
        self._executions[t] = {}
        return t

    def addElement(self, details: List[str],
                   faults: List[Any]) -> Spectrum.Element:
        e = Spectrum.Element(details, len(self._elements), faults)
        self._elements.append(e)
        self._groups[0].append(e)
        return e

    def addExecution(self, test: Spectrum.Test, elem: Spectrum.Element,
                     executed: bool):
        if (test not in self._executions):
            self._executions[test] = {}
        self._executions[test][elem] = executed
        # if (executed):
        #     if (test.outcome is Outcome.PASSED):
        #         self.p[elem] += 1
        #     else:
        #         self.f[elem] += 1

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
        spectrum = Spectrum(self._elements, self._groups, self._tests,
                            self._executions)
        return spectrum

    # def remove_unnecessary(self):
    #     """
    #     Remove the unnecessary elements that are within the groups from the
    #     spectrum.
    #     """
    #     remove = []
    #     for group in self._groups:
    #         remove.extend(group[1:])
    #         self.group_dict[group[0]] = group
    #     # remove.sort(reverse=True)
    #     # self.locs -= len(remove)
    #     for elem in remove:
    #         self.remove_element(elem)
