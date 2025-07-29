from __future__ import annotations
from typing import List, Dict, Any, Set, Sequence, Tuple, Callable, \
        Union, Iterable, Iterator, Optional, TYPE_CHECKING
from bitarray import bitarray
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
if TYPE_CHECKING:
    from flitsr.input import InputType

class Outcome(Enum):
    """ The outcome of a `Spectrum.Test` """
    PASSED = 0
    PASS = 0
    FAILED = 1
    FAIL = 1
    ERROR = 2


class Spectrum:
    """An implementation for a program spectrum."""
    class Test:
        """A test object holds information pertaining to a particular test."""

        __slots__ = ('name', 'index', 'outcome')

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

    class Entity(ABC, Iterable):
        """A generic spectrum `Spectrum.Entity`. This is the base class for `Spectrum.Element`
        and `Spectrum.Group` in the spectrum.
        """
        @abstractmethod
        def isFaulty(self) -> bool:
            """Returns whether or not this `Spectrum.Entity` pertains to a fault"""
            pass

        @abstractmethod
        def index(self) -> int:
            """The index of this `Spectrum.Entity`"""
            pass

        @abstractmethod
        def __len__(self) -> int:
            pass

        @abstractmethod
        def __iter__(self) -> Iterator:
            pass

        @abstractmethod
        def __getitem__(self, index: int) -> Spectrum.Element:
            pass

    class Element(Entity):
        """
        An element object holds information pertaining to a single spectral
        element (line, method, class, etc...).
        """
        __slots__ = ('_index', '_group', 'path', 'method', 'line', 'faults',
                     'tup')

        def __init__(self, details: List[str], index: int, faults: List[Any]):
            if (len(details) < 1):
                raise ValueError("Unnamed element: ", *details)
            self._index = index
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
            """Returns whether or not this `Spectrum.Element` pertains to a fault"""
            return len(self.faults) > 0

        def index(self) -> int:
            """Returns the index of this `Spectrum.Element`"""
            return self._index

        def __getitem__(self, index: int):
            if (index == 0):
                return self
            else:
                raise IndexError("list index out of range")

        def __iter__(self) -> Iterator:
            return iter((self,))

        def __len__(self) -> int:
            return 1

        def __str__(self):
            return "|".join(str(i) for i in self.tup if i) + \
                   (" (FAULT {})".format(",".join(str(x) for x in self.faults))
                    if self.faults else "")

        def output_str(self, type_: 'InputType', incl_faults=True) -> str:
            """
            Returns the string representation of this `Spectrum.Element` that can be
            used when writing out the spectrum in the given input type.

            Args:
              type_: 'InputType': The input type to render the output string for.
              incl_faults:  (Default value = True) Whether to include fault
                indicators in the output string

            Returns:
                The string representation of this `Spectrum.Element`

            """
            seps = type_.value.get_elem_separators()
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
            return (isinstance(other, Spectrum.Element) and
                    self._index == other._index)

        def __hash__(self):
            return self._index

        def semantic_eq(self, other) -> bool:
            """
            Variant of the __eq__ method for an `Spectrum.Element` that checks whether
            two elements are semantically equivalent.

            Args:
              other: The element to compare to

            Returns:
              True if this `Spectrum.Element` is equal to `other`, False otherwise.

            """
            return self.tup == other.tup

    class Group(Entity):
        """
        A spectral group is a collection of spectral elements which have
        identical spectra.
        """
        __slots__ = ('_elems', '_is_faulty', '_index')

        def __init__(self, elems: Optional[List[Spectrum.Element]] = None,
                     index: Optional[int] = None):
            """
            Create a group object. If elems is given, the group is initialized
            with the elements within, otherwise an empty group is initialized.
            """
            self._elems = elems if elems is not None else []
            self._is_faulty = any(e.isFaulty() for e in self._elems)
            self._index = index
            self._hash = hash(frozenset(self._elems))

        def sort_elems(self, key: Callable):
            """
            Sort the elements in this group by the given `key`.
            Args:
              key: Callable: The key to sort by
            """
            self._elems.sort(key=key)

        def set_index(self, index: int):
            """
            Set the index of this group. Used for spectrum execution lookup.
            NOTE: the group index MUST be unique for each group in a given
            spectrum.
            Args:
              index: int: The integer
            """
            self._index = index

        def index(self) -> int:
            """
            Get the index of this Group if available, otherwise raise an
            ``UnboundLocalError``.
            """
            if (self._index is None):
                raise UnboundLocalError("Group index has not been set")
            return self._index

        def isFaulty(self) -> bool:
            """
            Returns whether or not an element in this `Spectrum.Group` pertains to a
            fault
            """
            return self._is_faulty

        def is_subgroup(self, group: Spectrum.Group) -> bool:
            """
            Return whether the given `group` is a subgroup of this `Spectrum.Group`.
            Args:
              group: Spectrum.Group: The group to check.

            Returns:
              True if `group` is a subgroup of this `Spectrum.Group`, False otherwise.
            """
            for elem in group._elems:
                if (elem not in self):
                    return False
            return True

        def __getitem__(self, index: int) -> Spectrum.Element:
            return self._elems[index]

        def __len__(self):
            return len(self._elems)

        def __iter__(self):
            return iter(self._elems)

        def __str__(self) -> str:
            return f"G{self._index} ({self._elems})"

        def __repr__(self) -> str:
            return str(self)

        def __eq__(self, other):
            return (isinstance(other, Spectrum.Group) and
                    self._hash == other._hash)

        def __hash__(self):
            return self._hash

    class Execution():
        """The Execution object holds all of the spectral information pertaining
        to the execution of a particular test.
        """
        __slots__ = ('_groups', '_spectrum', 'exec', 'test', '_iter')

        def __init__(self, test: Spectrum.Test,
                     spectrum: Spectrum):
            self._groups = spectrum.groups()
            self._spectrum = spectrum
            self.exec = bitarray(len(self._groups))
            self.test = test

        def update(self, group: Spectrum.Group, executed: bool):
            """Update the execution information of a particular group

            Args:
              group: Spectrum.Group: The group to update information for
              executed: bool: The updated execution information; whether this
                  group is executed or not.
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
            Return the execution for the given `group` if it is available, else
            default.

            Args:
              group: Spectrum.Group: The `Spectrum.Group` to lookup.
              default: bool:  (Default value = False) The default value if
                `group` has no execution information in this `Spectrum.Execution`.

            Returns:
              The execution information for `group` if `group` is found,
              `default` otherwise.
            """
            try:
                return bool(self.exec[group.index()])
            except (KeyError, IndexError):
                return default

        def element_get(self, elem: Spectrum.Element,
                        default: bool = False) -> bool:
            """
            Similar to the `get` method, but takes an `Spectrum.Element` instead of a
            `Spectrum.Group`.

            Args:
              elem: Spectrum.Element: The `Spectrum.Element` to lookup.
              default: bool:  (Default value = False) The default value if
              `elem` has no execution information in this `Spectrum.Execution`.

            Returns:
              The execution information for `elem` if the `Spectrum.Group` of `elem` is
              found, `default` otherwise.
            """
            # Get the element's group
            try:
                return bool(self.exec[self._spectrum.get_group(elem).index()])
            except (KeyError, IndexError):
                return default

    def __init__(self, elements: List[Spectrum.Element],
                 groups: List[Spectrum.Group], tests: List[Spectrum.Test],
                 executions: Dict[Test, Set[Spectrum.Element]]):
        self.spectrum: Dict[Spectrum.Test, Spectrum.Execution] = {}
        self.p: Dict[Spectrum.Group, int] = dict()
        self.f: Dict[Spectrum.Group, int] = dict()
        # Initialize element related properties
        edict = {e: i for i, e in enumerate(elements)}
        for group in groups:
            group.sort_elems(key=lambda x: edict[x])
        self._groups = sorted(groups, key=lambda g: edict[g[0]])
        self._group_map: Dict[Spectrum.Element, Spectrum.Group] = {}
        for i, group in enumerate(self._groups):
            group.set_index(i)
            self.p[group] = 0
            self.f[group] = 0
            for elem in group:
                self._group_map[elem] = group
        self._elements: List[Spectrum.Element] = elements
        # Initialize test related properties
        self._removed_tests: Dict[str, List[Spectrum.Test]] = {}
        self._removed_groups: Dict[str, List[Spectrum.Group]] = {}
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
            self.spectrum[test] = self.Execution(test, self)
        # Initialize execution information
        for test in self._tests:
            test_exe = executions[test]
            seen: Set[Spectrum.Group] = set()
            for elem in test_exe:
                group = self._group_map[elem]
                if (group not in seen):
                    seen.add(group)
                    self.spectrum[test].update(group, True)
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

    def elements(self) -> List[Spectrum.Element]:
        """Get a list of a all the elements in this spectrum"""
        return self._elements

    def groups(self) -> List[Spectrum.Group]:
        """Get a list of a all the groups in this spectrum"""
        return self._groups

    def tests(self) -> List[Spectrum.Test]:
        """Get a list of a all the tests (passing and failing) in this spectrum"""
        return self._tests

    def failing(self) -> List[Spectrum.Test]:
        """Get a list of a all the failing tests in this spectrum"""
        return self._failing

    def locs(self) -> int:
        """Get the number of groups in this spectrum"""
        return len(self._groups)

    def remove_test(self, test: Spectrum.Test, bucket='default'):
        """
        Remove the given test from this spectrum.
        All removed tests are stored so that they may be added back to the
        spectrum at a later point. By default, removed tests are stored in the
        'default' bucket, but a different bucket name may be optionally given.
        Setting the bucket to be None will completely remove the test from the
        spectrum (NOTE: this does not save much memory, but only prevents the
        test from being restored by subsequent calls to reset).

        Args:
          test: Spectrum.Test: The `Spectrum.Test` to remove.
          bucket:  (Default value = 'default') The bucket to store the removed
            tests in.
        """
        if (test not in self._tests):
            return
        self._tests.remove(test)
        if (test.outcome is Outcome.PASSED):
            self.tp -= 1
        else:
            self._failing.remove(test)
            self.tf -= 1
        for group in self.groups():
            self.remove_execution(test, group, hard=False)
        if (bucket is not None):
            self._removed_tests.setdefault(bucket, []).append(test)

    def remove_execution(self, test: Spectrum.Test, ent: Spectrum.Entity,
                         hard=True):
        """
        Remove the execution of the given `Spectrum.Entity` in `test`.

        Args:
          test: Spectrum.Test: The test to remove the execution of `ent` from.
          ent: Spectrum.Entity: The `Spectrum.Entity` whose execution to remove.
          hard:  (Default value = True) Whether to remove this execution fully,
            i.e. even from the underlying spectrum
        """
        if (self.spectrum[test][ent]):
            if (isinstance(ent, Spectrum.Element)):
                group = self._group_map[ent]
            elif (isinstance(ent, Spectrum.Group)):
                group = ent
            if (hard):
                self.spectrum[test][group] = False
            if (test.outcome is Outcome.PASSED):
                self.p[group] -= 1
            else:
                self.f[group] -= 1

    def remove_group(self, group: Spectrum.Group, bucket='default'):
        """
        Remove the given `group` from the spectrum, and store it in the
        given `bucket`. See `Spectrum.remove_test` for a description of buckets.

        Args:
          group: Spectrum.Group: The `Spectrum.Group` to remove.
          bucket:  (Default value = 'default') The bucket to store the group in
            for later retrieval.
        """
        try:
            self._groups.remove(group)  # remove if there
            self._removed_groups.setdefault(bucket, []).append(group)
        except ValueError:
            # Ignore if the element is not in the list
            pass
        self.p.pop(group, None)  # remove if there
        self.f.pop(group, None)  # remove if there

    def reset(self, bucket: Union[None, str, List[str]] = None):
        """
        Re-activates removed tests and recomputes counts.
        By default, or if bucket is None, all buckets are emptied and their
        removed tests reactivated. A bucket name (or Iterable of bucket names)
        may optionally be given to only reset the given name(s).

        Args:
          bucket: Union[None: str: List[str]]:  (Default value = None) The
              bucket to reset.
        """
        # first get the groups to add back
        groups_add_back = []
        group_keys_remove = []
        for key in self._removed_groups:
            if (bucket is None or (isinstance(bucket, str) and key == bucket)
               or (isinstance(bucket, Iterable) and key in bucket)):
                groups_add_back.extend(self._removed_groups[key])
                group_keys_remove.append(key)
        for key in group_keys_remove:
            del self._removed_groups[key]
        # then add back the groups, re-computing counts
        for group in groups_add_back:
            self._groups.insert(group.index(), group)
            self.p[group] = len([t for t in self.tests() if t.outcome ==
                                Outcome.PASS and self[t][group]])
            self.f[group] = len([t for t in self.failing() if self[t][group]])
        # next get the tests to add back
        tests_add_back = []
        test_keys_remove = []
        for key in self._removed_tests:
            if (bucket is None or (isinstance(bucket, str) and key == bucket)
               or (isinstance(bucket, Iterable) and key in bucket)):
                tests_add_back.extend(self._removed_tests[key])
                test_keys_remove.append(key)
        for key in test_keys_remove:
            del self._removed_tests[key]
        # then add back the tests, re-computing counts
        for test in tests_add_back:
            self._add_back_removed_test(test)

    def _add_back_removed_test(self, test: Spectrum.Test):
        """
        Helper method to add back tests that have been removed from the
        spectrum.
        """
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

    def reset_single_test(self, test: Spectrum.Test,
                          bucket: Optional[str] = None):
        """
        Reset a single test that was stored in the given bucket. See the
        `Spectrum.reset` method, which is the iterative form of this one.

        Args:
          test: Spectrum.Test: The `Spectrum.Test` to reset.
          bucket: Optional[str]:  (Default value = None) The bucket that `test`
            is in, or ``None`` to check all buckets.

        Raises:
          KeyError: If the test could not be found in the given bucket.
        """
        if (bucket is None):
            for key in self._removed_tests:
                if (test in self._removed_tests[key]):
                    bucket = key
                    break
        if (bucket is None or test not in self._removed_tests[bucket]):
            raise KeyError(f"Could not find removed test {test} in "
                           f"{bucket or 'any'} bucket")
        self._removed_tests[bucket].remove(test)
        self._add_back_removed_test(test)

    def get_group(self, element: Spectrum.Element) -> Spectrum.Group:
        """
        Given an element, return the `Spectrum.Group` with identical coverage
        from this spectrum that this element is apart of.

        Args:
          element: Spectrum.Element: The `Spectrum.Element` to find the
            `Spectrum.Group` of.

        Returns:
          The group that the `element` belongs to.

        Raises:
          KeyError: If the element does not belong to any group in this
            spectrum.
        """
        return self._group_map[element]

    def get_faults(self) -> Dict[Any, Set[Spectrum.Element]]:
        """
        Returns a dictionary of all the faults in this spectrum, with the
        values being all the locations of each fault.
        """
        actual_faults: Dict[Any, Set[Spectrum.Element]] = dict()
        for group in self.groups():
            for elem in group:
                if (elem.faults):
                    for fault in elem.faults:
                        actual_faults.setdefault(fault, set()).add(elem)
        return actual_faults

    def get_tests(self, entity: Spectrum.Entity, only_failing=False,
                  remove=False, bucket='default') -> Set[Spectrum.Test]:
        """
        Finds all the test cases executing the given element, and (optionally)
        removes them from the spectrum. If removing tests from the spectrum, an
        optional bucket name may also be given.

        Args:
          entity: Spectrum.Entity: The entity to find tests for.
          only_failing:  (Default value = False) Whether to return only tests
              that are failing.
          remove:  (Default value = False) Whether to remove the found tests
              from the spectrum before returning them.
          bucket:  (Default value = 'default') The bucket to add the tests to
              if they are removed from the spectrum.

        Returns:
            The set of `Spectrum.Test` that `entity` is executed in.

        """
        executing = set()
        tests = self.failing() if only_failing else self.tests()
        for test in tests:
            if (self[test][entity]):
                executing.add(test)
        if (remove):
            for test in executing:
                self.remove_test(test, bucket=bucket)
        return executing

    def get_executed_groups(self, test: Spectrum.Test) -> Set[Spectrum.Group]:
        """
        Return the set of groups that are executed in the given `test`.

        Args:
          test: Spectrum.Test: The test whose executed groups to return.

        Returns:
          The set of `Spectrum.Group` that are executed in the given `test`.

        """
        return self._get_executed_entities(test, groups=True)

    def get_executed_elements(self, test: Spectrum.Test) -> Set[Spectrum.Element]:
        """
        Return the set of elements that are executed in the given `test`.

        Args:
          test: Spectrum.Test: The test whose executed elements to return.

        Returns:
          The set of `Spectrum.Element` that are executed in the given `test`.

        """
        return self._get_executed_entities(test, groups=False)

    def get_removed_tests(self, bucket='default') -> List[Spectrum.Test]:
        """
        Return a copy of all the removed tests in a particular bucket. If
        bucket is None, all removed tests from all buckets are returned.

        Args:
          bucket:  (Default value = 'default') The bucket to look for removed
            tests to return.

        Returns:
          A `List` of all the `Spectrum.Test` that were in the given bucket, or
          in all buckets if `bucket` is None.
        """
        if (bucket is None):
            return self._all_removed_tests()
        else:
            return self._removed_tests[bucket][:]

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

    def _all_removed_tests(self) -> List[Spectrum.Test]:
        """ Get a list of the removed tests in all buckets """
        all_removed = []
        for key in self._removed_tests:
            all_removed.extend(self._removed_tests[key])
        return all_removed

    def to_matrix(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Converts the current spectrum into a numpy matrix and error vector.

        Returns:
          A numpy matrix representing the spectrum, and numpy array
          representing the error vector.
        """
        # If no matrix already, create one
        if (not hasattr(self, '_matrix')):
            # Use all test cases and most elements
            self._matrix_tests = list(self.spectrum.keys())
            self._matrix_elems = list(self._groups)
            self._matrix = np.zeros((len(self._matrix_tests),
                                     len(self._matrix_elems)),
                                    dtype=bool)
            self._errVector = np.zeros(len(self._matrix_tests),
                                       dtype=bool)
            for (i, test) in enumerate(self._matrix_tests):
                for (j, elem) in enumerate(self._matrix_elems):
                    self._matrix[i][j] = self.spectrum[test][elem]
                self._errVector[i] = 0 if (test.outcome is
                                           Outcome.PASSED) else 1
        # Extract submatrix
        test_set = set(self._tests)
        tmask = np.array([item in test_set for item in self._matrix_tests])
        # tmask = np.isin(self._matrix_tests, self._tests)
        group_set = set(self._groups)
        emask = np.array([item in group_set for item in self._matrix_elems])
        # emask = np.isin(self._matrix_elems, self._groups)
        matrix = self._matrix[np.ix_(tmask, emask)]
        errVector = self._errVector[tmask]
        return matrix, errVector

    def search_tests(self, name_part,
                     incl_removed=False) -> List[Spectrum.Test]:
        """
        Searches for any test that matches the partial test name `name_part`.
        Returns a list of all the matches.

        Args:
          name_part: The partial name of a test to search for.
          incl_removed:  (Default value = False) Whether to include tests that
            have been removed.

        Returns:
          A list of all the tests that match `name_part`.
        """
        results = [t for t in self.tests() if t.name.find(name_part) != -1]
        if (incl_removed):
            results.extend([t for t in self._all_removed_tests()
                            if t.name.find(name_part) != -1])
        return results

    def search_elements(self, name_part, groups=False) \
            -> List[Union[Spectrum.Element, Spectrum.Group]]:
        """
        Searches for any element that matches the partial element name
        `name_part`. Returns a list of all the matches.

        Args:
          name_part: The partial name of an entity to search for.
          groups:  (Default value = False) Whether to search for
            `Spectrum.Group` or `Spectrum.Element`.

        Returns:
          A list of all the entitied that match `name_part`.
        """
        elems = self._groups if groups else self._elements
        results = [e for e in elems if str(e).find(name_part) != -1]
        return results
