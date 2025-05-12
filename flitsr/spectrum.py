from __future__ import annotations
from typing import List, Dict, Any, Set, Sequence, Tuple
from bitarray import bitarray
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from flitsr.const_iter import ConstIter
from flitsr.input_type import InputType
from flitsr.errors import error


class Outcome(Enum):
    PASSED = 0
    PASS = 0
    FAILED = 1
    FAIL = 1
    ERROR = 2


class Spectrum:
    """An implementation for a program spectrum."""
    class Test:
        """A test object holds information pertaining to a particular test."""
        def __init__(self, name: str, index: int, outcome: Outcome):
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

    class Entity(ABC):
        @abstractmethod
        def isFaulty(self) -> bool:
            pass

        @abstractmethod
        def index(self) -> int:
            pass

    class Element(Entity):
        """
        An element object holds information pertaining to a single spectral
        element (line, method, class, etc...).
        """
        def __init__(self, details: List[str], index: int, faults: List[Any],
                     group: Spectrum.Group = None):
            if (len(details) < 1):
                raise ValueError("Unnamed element: ", *details)
            self._index = index
            self._group = group
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
            # self.hash = hash(self.tup)

        def isFaulty(self) -> bool:
            return len(self.faults) > 0

        def index(self) -> int:
            return self._index

        def set_group(self, group: Spectrum.Group):
            self._group = group

        def group(self) -> Spectrum.Group:
            if (self._group is None):
                raise UnboundLocalError("Element group has not been set")
            return self._group

        def __str__(self):
            return "|".join(str(i) for i in self.tup if i) + \
                   (" (FAULT {})".format(",".join(str(x) for x in self.faults))
                    if self.faults else "")

        def output_str(self, type_: InputType, incl_faults=True) -> str:
            if (type_ is InputType.TCM):
                seps = ['.', ':', ':', ' | ']
            elif (type_ is InputType.GZOLTAR):
                seps = ['$', '#', ':', ':']
            else:
                error(f"Input type {type_} not supported for output string")
            gstring = ''
            path_part = self.path.rpartition('.')
            if (path_part[0] != '' and path_part[2] != ''):
                gstring = path_part[0] + seps[0] + path_part[2]
            elif (path_part[0] != '' or path_part[2] != ''):
                gstring = path_part[0] + path_part[2]
            if (self.method):
                gstring += (seps[1] if (gstring != '') else '') + self.method
            if (self.line):
                gstring += (seps[2] if (gstring != '') else '') + str(self.line)
            if (incl_faults and self.isFaulty()):
                gstring += seps[3] + seps[3].join(str(x) for x in self.faults)
            return gstring

        def __repr__(self):
            return str(self)

        def __eq__(self, other):
            return self._index == other._index

        def __hash__(self):
            return self._index

    class Group(Entity):
        """
        A spectral group is a collection of spectral elements which have
        identical spectra.
        """
        def __init__(self, elems: List[Spectrum.Element] = None,
                     index: int = None):
            """
            Create a group object. If elems is given, the group is initialized
            with the elements within, otherwise an empty group is initialized.
            """
            self._elems = elems if elems is not None else []
            self._is_faulty = any(e.isFaulty() for e in self._elems)
            self._index = index

        def append(self, element: Spectrum.Element):
            self._elems.append(element)

        def set_index(self, index: int):
            self._index = index

        def index(self) -> int:
            if (self._index is None):
                raise UnboundLocalError("Group index has not been set")
            return self._index

        def isFaulty(self) -> bool:
            return self._is_faulty

        def get_elements(self) -> List[Spectrum.Element]:
            return self._elems

        def is_in(self, element):
            return element in self._elems

        def __str__(self) -> str:
            return f"G{self._index} ({self._elems})"

        def __repr__(self) -> str:
            return str(self)

        def __eq__(self, other):
            return self._index == other._index

        def __hash__(self):
            return self._index

    class Execution():
        """
        The Execution object holds all of the spectral information pertaining
        to the execution of a particular test.
        """

        def __init__(self, test: Spectrum.Test,
                     groups: List[Spectrum.Group]):
            self._groups = groups
            self.exec = bitarray(len(self._groups))
            self.test = test

        def update(self, group: Spectrum.Group, executed: bool):
            """
            Update the execution information of a particular group
            """
            self.exec[group.index()] = executed

        def __len__(self):
            return len(self._groups)

        def __iter__(self):
            self._iter = iter(self._groups)
            return self

        def __next__(self):
            return self.get(next(self._iter))

        def __getitem__(self, elem: Spectrum.Entity) -> bool:
            if (isinstance(elem, Spectrum.Group)):
                return self.get(elem, False)
            elif (isinstance(elem, Spectrum.Element)):
                return self.element_get(elem, False)
            else:
                raise TypeError(f"Illegal Entity type: {type(elem).__name__}")

        def __setitem__(self, group: Spectrum.Group, val: bool):
            try:
                self.exec[group.index()] = val
            except KeyError:
                pass

        def get(self, group: Spectrum.Group, default: bool = False) -> bool:
            """
            Return the execution information for the given ambiguity group. If
            the element is not present in the execution, default is given.
            """
            try:
                return bool(self.exec[group.index()])
            except (KeyError, IndexError):
                return default

        def element_get(self, elem: Spectrum.Element,
                        default: bool = False) -> bool:
            """
            Return the execution information for the given element. If the
            element is not present in the execution, default is given.
            """
            # Get the element's group
            try:
                return bool(self.exec[elem.group().index()])
            except (KeyError, IndexError):
                return default

    def __init__(self, elements: List[Spectrum.Element],
                 groups: List[Spectrum.Group], tests: List[Spectrum.Test],
                 executions: Dict[Test, Dict[Element, bool]]):
        self.spectrum: Dict[Spectrum.Test, Spectrum.Execution] = {}
        self.p: Dict[Spectrum.Group, int] = dict()
        self.f: Dict[Spectrum.Group, int] = dict()
        # Initialize element related properties
        edict = {e: i for i, e in enumerate(elements)}
        self._groups = sorted(groups, key=lambda g: edict[g.get_elements()[0]])
        for i, group in enumerate(self._groups):
            group.set_index(i)
            self.p[group] = 0
            self.f[group] = 0
            for elem in group.get_elements():
                elem.set_group(group)
        self._elements: List[Spectrum.Element] = elements
        # Initialize test related properties
        self._removed: List[Spectrum.Test] = []
        self._tests: List[Spectrum.Test] = tests
        self._failing: List[Spectrum.Test] = []
        self.tp: int = 0
        self.tf: int = 0
        for test in tests:
            # Increment total counts & add to failing set
            if (test.outcome is Outcome.PASSED):
                self.tp += 1
            else:
                self._failing.append(test)
                self.tf += 1
            # Add test execution
            self.spectrum[test] = self.Execution(test, self._groups)
        # Initialize execution information
        for test in self._tests:
            test_exe = executions[test]
            seen: Set[Spectrum.Group] = set()
            for elem, exe in test_exe.items():
                group = elem.group()
                if (group not in seen):
                    seen.add(group)
                    self.spectrum[test].update(group, exe)
                    if (test.outcome is Outcome.PASSED):
                        self.p[group] += 1
                    else:
                        self.f[group] += 1

    def __getitem__(self, t: Test):
        return self.spectrum[t]

    def __iter__(self):
        self._iter = iter(self._tests)
        return self

    def __next__(self):
        return self.spectrum[next(self._iter)]

    def __len__(self):
        return len(self._tests)

    # def elements(self) -> List[Spectrum.Element]:
    #     return self._elements

    def groups(self) -> List[Spectrum.Group]:
        return self._groups

    def tests(self) -> List[Spectrum.Test]:
        return self._tests

    def failing(self) -> List[Spectrum.Test]:
        return self._failing

    def locs(self) -> int:
        return len(self._groups)

    def remove(self, test: Spectrum.Test, hard=False):
        self._tests.remove(test)
        if (test.outcome is Outcome.PASSED):
            self.tp -= 1
        else:
            self._failing.remove(test)
            self.tf -= 1
        for group in self.groups():
            self.remove_execution(test, group, hard=False)
        if (not hard):
            self._removed.append(test)

    def remove_execution(self, test: Spectrum.Test, ent: Spectrum.Entity,
                         hard=True):
        if (self.spectrum[test][ent]):
            if (isinstance(ent, Spectrum.Element)):
                group = ent.group()
            elif (isinstance(ent, Spectrum.Group)):
                group = ent
            if (hard):
                self.spectrum[test][group] = False
            if (test.outcome is Outcome.PASSED):
                self.p[group] -= 1
            else:
                self.f[group] -= 1

    def remove_group(self, group: Spectrum.Group):
        try:
            self._groups.remove(group)  # remove if there
        except ValueError:
            # Ignore if the element is not in the list
            pass
        self.p.pop(group, None)  # remove if there
        self.f.pop(group, None)  # remove if there
        # No need to remove execution (bitarray)
        # for test in self.tests():
        #     self.spectrum[test].remove_exec(rem)  # remove if there
        return group

    def reset(self):
        """Re-activates all the tests and recomputes counts"""
        for test in self._removed:
            self._tests.append(test)
            if (test.outcome is Outcome.PASSED):
                self.tp += 1
            else:
                self._failing.append(test)
                self.tf += 1
            for group in self.groups():
                if (self.spectrum[test][group]):
                    if (test.outcome is Outcome.PASSED):
                        self.p[group] += 1
                    else:
                        self.f[group] += 1
        self._removed.clear()

    def get_group(self, elem: Spectrum.Element) -> Spectrum.Group:
        """
        Given an element, return the group of elements with identical coverage
        that this element is apart of.
        """
        return elem.group()

    def get_faults(self) -> Dict[Any, List[Spectrum.Element]]:
        actual_faults: Dict[Any, List[Spectrum.Element]] = dict()
        for group in self.groups():
            for elem in group.get_elements():
                if (elem.faults):
                    for fault in elem.faults:
                        if (fault not in actual_faults):
                            actual_faults[fault] = []
                        actual_faults[fault].append(elem)
        return actual_faults

    def get_tests(self, entity: Spectrum.Entity, only_failing=False,
                  remove=False) -> Set[Spectrum.Test]:
        """
        Finds all the test cases executing the given element, and (optionally)
        removes them from the spectrum.
        """
        executing = set()
        tests = self.failing() if only_failing else self.tests()
        for test in tests:
            if (self[test][entity]):
                executing.add(test)
        if (remove):
            for test in executing:
                self.remove(test)
        return executing

    def get_executed_groups(self, test: Spectrum.Test) -> Set[Spectrum.Group]:
        return self._get_executed_entities(test, groups=True)

    def get_executed_elements(self, test: Spectrum.Test) -> Set[Spectrum.Element]:
        return self._get_executed_entities(test, groups=False)

    def _get_executed_entities(self, test: Spectrum.Test, groups=True):
        """
        Finds either the groups (default) or the elements (groups = False)
        executed in the given test.
        """
        executed = set()
        entities: Sequence[Spectrum.Entity]
        if (groups):
            entities = self._groups
        else:
            entities = self._elements
        for ent in entities:
            if (self[test][ent]):
                executed.add(ent)
        return executed

    def to_matrix(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Converts the current spectrum into a numpy matrix and error vector.
        """
        # If no matrix already, create one
        if (not hasattr(self, '_matrix')):
            # Use all test cases and most elements
            self._matrix_tests = np.array(list(self.spectrum.keys()))
            self._matrix_elems = np.array(list(self._groups))
            self._matrix = np.zeros((len(self._matrix_tests),
                                     len(self._matrix_elems)))
            self._errVector = np.zeros(len(self._matrix_tests))
            for (i, test) in enumerate(self._matrix_tests):
                for (j, elem) in enumerate(self._matrix_elems):
                    self._matrix[i][j] = self.spectrum[test][elem]
                self._errVector[i] = 0 if (test.outcome is Outcome.PASSED) else 1
        # Extract submatrix
        tmask = np.isin(self._matrix_tests, self._tests)
        emask = np.isin(self._matrix_elems, self._groups)
        matrix = self._matrix[np.ix_(tmask, emask)]
        errVector = self._errVector[tmask]
        return matrix, errVector

    def search_tests(self, name_part, incl_removed=False):
        """
        Searches for any test that matches the partial test name `name_part`.
        Returns a list of all the matches.
        """
        results = [t for t in self.tests() if t.name.find(name_part) != -1]
        if (incl_removed):
            results.extend([t for t in self._removed
                            if t.name.find(name_part) != -1])
        return results

    def search_elements(self, name_part, groups=False):
        """
        Searches for any element that matches the partial element name
        `name_part`. Returns a list of all the matches.
        """
        elems = self._groups if groups else self._elements
        results = [e for e in elems if str(e).find(name_part) != -1]
        return results
