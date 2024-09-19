from __future__ import annotations
from typing import List, Dict, Any, Set
from bitarray import bitarray
import numpy as np
from flitsr.const_iter import ConstIter


class Spectrum():
    """An implementation for a program spectrum."""
    class Test():
        """A test object holds information pertaining to a particular test."""
        def __init__(self, name: str, index: int, outcome: bool):
            self.name = name
            self.index = index
            self.outcome = outcome

        def __str__(self):
            return self.name

        def __repr__(self):
            return str(self)

        def __eq__(self, other):
            return self.name == other.name

        def __hash__(self):
            return hash(self.name)

    class Element():
        """
        An element object holds information pertaining to a single spectral
        element (line, method, class, etc...).
        """
        def __init__(self, details: List[str], faults: List[Any]):
            if (len(details) < 1):
                raise ValueError("Unnamed element: ", *details)
            self.path = details[0]
            self.method = None
            self.line = None
            if (len(details) > 2):
                if (details[2].isdigit()):
                    self.line = int(details[2])
                    self.method = details[1]
                else:
                    self.method = details[1] + "|" + details[2]
            elif (len(details) > 1):
                if (not details[1].isdigit()):
                    self.method = details[1]
                else:
                    self.line = int(details[1])
            self.faults = faults
            self.tup = (self.path, self.method, self.line)
            self.hash = hash(self.tup)

        def isFaulty(self) -> bool:
            return len(self.faults) > 0

        def __str__(self):
            return "|".join(str(i) for i in self.tup if i) + " " + \
                   ("(FAULT {})".format(",".join(str(x) for x in self.faults))
                    if self.faults else "")

        def gzoltar_str(self) -> str:
            gstring = ''
            path_part = self.path.rpartition('.')
            if (path_part[0] != '' and path_part[2] != ''):
                gstring = path_part[0] + '$' + path_part[2]
            elif (path_part[0] != '' or path_part[2] != ''):
                gstring = path_part[0] + path_part[2]
            if (self.method):
                gstring += ('#' if (gstring != '') else '') + self.method
            if (self.line):
                gstring += (':' if (gstring != '') else '') + str(self.line)
            if (self.isFaulty()):
                gstring += ':' + ':'.join(str(x) for x in self.faults)
            return gstring

        def __repr__(self):
            return str(self)

        def __eq__(self, other):
            return self.tup == other.tup

        def __hash__(self):
            return self.hash

    class Execution():
        """
        The Execution object holds all of the spectral information pertaining
        to the execution of a particular test.
        """

        def __init__(self, test: Spectrum.Test,
                     all_elems: Dict[Spectrum.Element, int],
                     cur_elems: List[Spectrum.Element]):
            self.elems = all_elems
            self._cur_elems = cur_elems
            self.exec = bitarray(len(self.elems))
            self.test = test

        def addElement(self, elem: Spectrum.Element, executed: bool):
            # Extend the exec array if the elems map has been updated
            if (len(self.elems) != len(self.exec)):
                self.exec.extend(ConstIter(len(self.elems)-len(self.exec)))
            self.exec[self.elems[elem]] = executed

        def __len__(self):
            return len(self._cur_elems)

        def __iter__(self):
            self._iter = iter(self._cur_elems)
            return self

        def __next__(self):
            return self.get(next(self._iter))

        def __getitem__(self, elem: Spectrum.Element):
            return self.get(elem, False)

        def __setitem__(self, elem: Spectrum.Element, val: bool):
            try:
                self.exec[self.elems[elem]] = val
            except KeyError:
                pass

        def get(self, elem: Spectrum.Element, default=False) -> bool:
            try:
                return bool(self.exec[self.elems[elem]])
            except KeyError:
                return default

    def __init__(self):
        self.spectrum: Dict[Spectrum.Test, Spectrum.Execution] = {}
        self._tests: List[Spectrum.Test] = []
        self._failing: List[Spectrum.Test] = []
        self._curr_elements: List[Spectrum.Element] = []
        self._full_elements: Dict[Spectrum.Element, int] = {}
        self.p: Dict[Spectrum.Element, int] = dict()
        self.f: Dict[Spectrum.Element, int] = dict()
        self.tp: int = 0
        self.tf: int = 0
        self.groups: List[List[Spectrum.Element]] = [[]]
        self.group_dict: Dict[Spectrum.Element, List[Spectrum.Element]] = {}
        self.removed: List[Spectrum.Test] = []

    def __getitem__(self, t: Test):
        return self.spectrum[t]

    def __iter__(self):
        self._iter = iter(self._tests)
        return self

    def __next__(self):
        return self.spectrum[next(self._iter)]

    def __len__(self):
        return len(self._tests)

    def elements(self):
        return self._curr_elements

    def tests(self):
        return self._tests

    def failing(self):
        return self._failing

    def locs(self):
        return len(self._curr_elements)

    def remove(self, test: Spectrum.Test, hard=False):
        self._tests.remove(test)
        if (test.outcome is True):
            self.tp -= 1
        else:
            self._failing.remove(test)
            self.tf -= 1
        for elem in self.elements():
            self.remove_execution(test, elem, hard=False)
        if (not hard):
            self.removed.append(test)

    def remove_execution(self, test: Spectrum.Test, elem: Spectrum.Element,
                         hard=True):
        if (self.spectrum[test][elem]):
            if (hard):
                self.spectrum[test][elem] = False
            if (test.outcome is True):
                self.p[elem] -= 1
            else:
                self.f[elem] -= 1

    def remove_element(self, element: Spectrum.Element):
        try:
            self._curr_elements.remove(element)  # remove if there
        except ValueError:
            # Ignore if the element is not in the list
            pass
        self.p.pop(element, None)  # remove if there
        self.f.pop(element, None)  # remove if there
        # No need to remove execution (bitarray)
        # for test in self.tests():
        #     self.spectrum[test].remove_exec(rem)  # remove if there
        return element

    def reset(self):
        """Re-activates all the tests and recomputes counts"""
        for test in self.removed:
            self._tests.append(test)
            if (test.outcome is True):
                self.tp += 1
            else:
                self._failing.append(test)
                self.tf += 1
            for elem in self.elements():
                if (self.spectrum[test][elem]):
                    if (test.outcome is True):
                        self.p[elem] += 1
                    else:
                        self.f[elem] += 1
        self.removed.clear()

    def addTest(self, name: str, index: int, outcome: bool):
        t = self.Test(name, index, outcome)
        self._tests.append(t)
        if (outcome is False):
            self._failing.append(t)
        self.spectrum[t] = self.Execution(t, self._full_elements,
                                          self._curr_elements)
        # Increment total counts
        if (outcome):
            self.tp += 1
        else:
            self.tf += 1

    def addElement(self, details: List[str], faults: List[Any]) -> Element:
        e = self.Element(details, faults)
        self._full_elements[e] = len(self._full_elements)
        self._curr_elements.append(e)
        self.groups[0].append(e)
        self.f[e] = 0
        self.p[e] = 0
        return e

    def addExecution(self, test: Test, elem: Element, executed: bool):
        self.spectrum[test].addElement(elem, executed)
        if (executed):
            if (test.outcome):
                self.p[elem] += 1
            else:
                self.f[elem] += 1

    def split_groups_on_test(self, test: Test):
        """
        Given one test pertaining to a row in the spectrum, split the groups
        according to the coverage. The split will potentially split each group
        in half, based on those elements that are executed in the test, and
        those that are not.
        """
        row = self.spectrum[test]
        new_groups = []
        for group in self.groups:
            first = row[group[0]]
            eq = [group[0]]
            neq = []
            for elem in group[1:]:
                if (row[elem] == first):
                    eq.append(elem)
                else:
                    neq.append(elem)
            new_groups.append(eq)
            if (neq != []):
                new_groups.append(neq)
        self.groups = new_groups

    def remove_unnecessary(self):
        """
        Remove the unnecessary elements that are within the groups from the
        spectrum.
        """
        remove = []
        for group in self.groups:
            remove.extend(group[1:])
            self.group_dict[group[0]] = group
        # remove.sort(reverse=True)
        # self.locs -= len(remove)
        for elem in remove:
            self.remove_element(elem)

    def get_group(self, elem: Spectrum.Element) -> List[Spectrum.Element]:
        """
        Given an element, return the group of elements with identical coverage
        that this element is apart of.
        """
        # Faster way for exposed elements
        if (elem in self.group_dict):
            return self.group_dict[elem]
        # Slower way for un-exposed elements
        for group in self.groups:
            if (elem in group):
                return group
        # Error if not found in either way
        raise KeyError("Element \""+str(elem)+"\" not found in a spectrum group")

    def get_faults(self) -> Dict[Any, List[Spectrum.Element]]:
        actual_faults: Dict[Any, List[Spectrum.Element]] = dict()
        for group in self.groups:
            for elem in group:
                if (elem.faults):
                    for fault in elem.faults:
                        if (fault not in actual_faults):
                            actual_faults[fault] = []
                        actual_faults[fault].append(elem)
        return actual_faults

    def get_tests(self, element: Spectrum.Element, only_failing=False,
                  remove=False) -> Set[Spectrum.Test]:
        """
        Finds all the test cases executing the given element, and (optionally)
        removes them from the spectrum.
        """
        executing = set()
        tests = self.failing() if only_failing else self.tests()
        for test in tests:
            if (self[test][element]):
                executing.add(test)
        if (remove):
            for test in executing:
                self.remove(test)
        return executing

    def to_matrix(self):
        """
        Converts the current spectrum into a numpy matrix and error vector.
        """
        # If no matrix already, create one
        if (not hasattr(self, '_matrix')):
            # Use all test cases and most elements
            self._matrix_tests = np.array(list(self.spectrum.keys()))
            self._matrix_elems = np.array(list(self._curr_elements))
            self._matrix = np.zeros((len(self._matrix_tests),
                                     len(self._matrix_elems)))
            self._errVector = np.zeros(len(self._matrix_tests))
            for (i, test) in enumerate(self._matrix_tests):
                for (j, elem) in enumerate(self._matrix_elems):
                    self._matrix[i][j] = self.spectrum[test][elem]
                self._errVector[i] = 1 if (test.outcome is False) else 0
        # Extract submatrix
        tmask = np.isin(self._matrix_tests, self._tests)
        emask = np.isin(self._matrix_elems, self._curr_elements)
        matrix = self._matrix[np.ix_(tmask, emask)]
        errVector = self._errVector[tmask]
        return matrix, errVector
