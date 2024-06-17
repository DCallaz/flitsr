from __future__ import annotations
from typing import List, Dict, Any
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

        def isFaulty(self):
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

        def __next__(self):
            return self.elems.__next__()

        def __getitem__(self, elem: Spectrum.Element):
            return self.get(elem, False)

        def __setitem__(self, elem: Spectrum.Element, val: bool):
            try:
                self.exec[self.elems[elem]] = val
            except KeyError:
                pass

        def get(self, elem: Spectrum.Element, default=False):
            try:
                return self.exec[self.elems[elem]]
            except KeyError:
                return default

    def __init__(self) -> None:
        self.spectrum: Dict[Spectrum.Test, Spectrum.Execution] = {}
        self.tests: List[Spectrum.Test] = []
        self.failing: List[Spectrum.Test] = []
        self.elements: Dict[Spectrum.Element, int] = {}
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
        self.spectrum[t] = self.Execution(t, self.elements)
        # Increment total counts
        if (outcome):
            self.tp += 1
        else:
            self.tf += 1

    def addElement(self, details: List[str], faults: List[int]):
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

    def merge_on_test(self, test: Test):
        """Given one test pertaining to a row in the spectrum, merge the groups"""
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
        # remove.sort(reverse=True)
        # self.locs -= len(remove)
        for rem in remove:
            self.elements.pop(rem, None)  # remove if there
            self.p.pop(rem, None)  # remove if there
            self.f.pop(rem, None)  # remove if there
            # No need to remove execution (bitarray)
            # for test in self.tests:
            #     self.spectrum[test].remove_exec(rem)  # remove if there
