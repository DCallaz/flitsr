from __future__ import annotations
from typing import List, Dict, Any, Set
from bitarray import bitarray
from flitsr.const_iter import ConstIter


class Spectrum():
    """An implementation for a program spectrum."""
    class Test():
        """A test object holds information pertaining to a particular test."""
        def __init__(self, name: str, outcome: bool):
            self.name = name
            self.outcome = outcome

        def __str__(self):
            return self.name

        def __repr__(self):
            return str(self)

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
                     elems: Dict[Spectrum.Element, int]):
            self.elems = elems
            self.exec = bitarray(len(self.elems))
            self.test = test

        def addElement(self, elem: Spectrum.Element, executed: bool):
            # Extend the exec array if the elems map has been updated
            if (len(self.elems) != len(self.exec)):
                self.exec.extend(ConstIter(len(self.elems)-len(self.exec)))
            self.exec[self.elems[elem]] = executed

        def __len__(self):
            return len(self.elems)

        def __iter__(self):
            return self.elems.__iter__()

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
        self.tests: List[Spectrum.Test] = []
        self.failing: List[Spectrum.Test] = []
        self.elements: Dict[Spectrum.Element, int] = {}
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
        return self.failing.__iter__()

    def locs(self):
        return len(self.elements)

    def remove(self, test: Spectrum.Test, hard=False):
        self.tests.remove(test)
        if (test.outcome is True):
            self.tp -= 1
        else:
            self.failing.remove(test)
            self.tf -= 1
        for elem in self.elements:
            if (self.spectrum[test][elem]):
                if (test.outcome is True):
                    self.p[elem] -= 1
                else:
                    self.f[elem] -= 1
        if (not hard):
            self.removed.append(test)

    def remove_execution(self, test: Spectrum.Test, elem: Spectrum.Element):
        if (self.spectrum[test][elem]):
            self.spectrum[test][elem] = False
            if (test.outcome is True):
                self.p[elem] -= 1
            else:
                self.f[elem] -= 1
        else:
            raise ValueError("Cannot remove an execution that does not exist")

    def remove_element(self, element: Spectrum.Element):
        self.elements.pop(element, None)  # remove if there
        self.p.pop(element, None)  # remove if there
        self.f.pop(element, None)  # remove if there
        # No need to remove execution (bitarray)
        # for test in self.tests:
        #     self.spectrum[test].remove_exec(rem)  # remove if there
        return element

    def reset(self):
        """Re-activates all the tests and recomputes counts"""
        for test in self.removed:
            self.tests.append(test)
            if (test.outcome is True):
                self.tp += 1
            else:
                self.failing.append(test)
                self.tf += 1
            for elem in self.elements:
                if (self.spectrum[test][elem]):
                    if (test.outcome is True):
                        self.p[elem] += 1
                    else:
                        self.f[elem] += 1
        self.removed.clear()

    def addTest(self, name: str, outcome: bool):
        t = self.Test(name, outcome)
        self.tests.append(t)
        if (outcome is False):
            self.failing.append(t)
        self.spectrum[t] = self.Execution(t, self.elements)
        # Increment total counts
        if (outcome):
            self.tp += 1
        else:
            self.tf += 1

    def addElement(self, details: List[str], faults: List[int]) -> Element:
        e = self.Element(details, faults)
        self.elements[e] = len(self.elements)
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

    def get_faults(self) -> Dict[int, List[Spectrum.Element]]:
        actual_faults: Dict[int, List[Spectrum.Element]] = dict()
        for group in self.groups:
            for elem in group:
                if (elem.faults):
                    for fault in elem.faults:
                        if (fault not in actual_faults):
                            actual_faults[fault] = []
                        actual_faults[fault].append(elem)
        return actual_faults

    def get_fault_groups(self) -> Dict[int, Set[int]]:
        faults = self.get_faults()
        fault_groups: Dict[int, Set[int]] = {}
        for i in range(len(self.groups)):
            for (fault_num, fault_locs) in faults.items():
                for fault_loc in fault_locs:
                    if (fault_loc in self.groups[i]):
                        if (fault_num not in fault_groups):
                            fault_groups[fault_num] = set()
                        fault_groups[fault_num].add(i)
                        break
        return fault_groups
