from __future__ import annotations
from typing import List, Dict


class Spectrum():
    """
    An implementation for a program spectrum.
    """
    class Test():
        """
        A test object holds information pertaining to a particular test.
        """
        def __init__(self, name: str, outcome: bool):
            self.name = name
            self.outcome = outcome

        def __str__(self):
            return self.name

    class Element():
        """
        An element object holds information pertaining to a single spectral
        element (line, method, class, etc...).
        """
        def __init__(self, details, faults):
            self.details = details
            # if (type(details, str) or len(details) == 1):
            #  self.name = details[0]
            self.faults = faults

        def isFaulty(self):
            return len(self.faults) > 0

        def __str__(self):
            return "|".join(self.details) + " " + \
                   ("(FAULT {})".format(",".join(str(x) for x in self.faults))
                    if self.faults else "")

    class Execution():
        """
        The Execution object holds all of the spectral information pertaining
        to the execution of a particular test.
        """
        def __init__(self, test: Spectrum.Test):
            self.elems: List[Spectrum.Element] = []
            self.exec: Dict[Spectrum.Element, bool] = {}
            self.test = test

        def addElement(self, elem: Spectrum.Element, executed: bool):
            self.elems.append(elem)
            self.exec[elem] = executed

        def __iter__(self):
            return self.elems.__iter__()

        def __next__(self):
            return self.elems.__next__()

        def __getitem__(self, elem: Spectrum.Element):
            return self.exec[elem]

        def pop(self, elem, *args):
            return self.exec.pop(elem, *args)

    def __init__(self) -> None:
        self.spectrum: Dict[Spectrum.Test, Spectrum.Execution] = {}
        self.tests: List[Spectrum.Test] = []
        self.failing: List[Spectrum.Test] = []
        self.elements: List[Spectrum.Element] = []
        self.p: Dict[Spectrum.Element, int] = dict()
        self.f: Dict[Spectrum.Element, int] = dict()
        self.tp: int = 0
        self.tf: int = 0
        self.groups: List[List[Spectrum.Element]] = [[]]
        self.removed: List[Spectrum.Test] = []

    def __getitem__(self, t: Test):
        return self.spectrum[t]

    def __iter__(self):
        return self.failing.__iter__()

    def __next__(self):
        return self.failing.__next__()

    def locs(self):
        return len(self.elements)

    def remove(self, test: Spectrum.Test, hard=False):
        self.tests.remove(test)
        if (test in self.failing):
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
        self.spectrum[t] = self.Execution(t)

    def addElement(self, details: List[str], faults: List[int]):
        e = self.Element(details, faults)
        self.elements.append(e)
        self.groups[0].append(e)
        self.f[e] = 0
        self.p[e] = 0
        return e

    def addExecution(self, test: Test, elem: Element, executed: bool):
        self.spectrum[test].addElement(elem, executed)

    def merge_on_test(self, test):
        """Given one test pertaining to a row in the table, merge the groups"""
        row = self.spectrum[test]
        new_groups = []
        for group in self.groups:
            eq = [group[0]]
            neq = []
            for elem in group[1:]:
                if (row[elem] == row[group[0]]):
                    eq.append(elem)
                else:
                    neq.append(elem)
            if (eq != []):
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
        # remove.sort(reverse=True)
        # self.locs -= len(remove)
        for rem in remove:
            self.elements.remove(rem)
            self.p.pop(rem)
            self.f.pop(rem)
            for test in self.tests:
                self.spectrum[test].pop(rem, None)
