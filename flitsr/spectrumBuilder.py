from typing import List, Dict, Any, Set, Tuple, Union
from flitsr.spectrum import Spectrum, Outcome


class SpectrumBuilder:
    """ Builds a `Spectrum <flitsr.spectrum.Spectrum>` object."""

    def __init__(self, collapse_methods: bool = False):
        """
        Constructs a `SpectrumBuilder` object to facilitate building a
        `Spectrum <flitsr.spectrum.Spectrum>`.

        Args:
          collapse_methods: bool: (Default value = False) Whether to form a
            method level spectrum.
        """
        self._collapse_methods = collapse_methods
        self._method_map: Dict[int, Spectrum.Element] = {}
        self._methods: Dict[Tuple[str, str], Spectrum.Element] = {}
        self._elements: List[Spectrum.Element] = []
        self._tests: Dict[int, Spectrum.Test] = {}
        self._executions: Dict[Spectrum.Test, Set[Spectrum.Element]] = {}

    def get_tests(self) -> List[Spectrum.Test]:
        """ Return the current list of Tests. """
        return [self._tests[key] for key in sorted(self._tests.keys())]

    def getElement(self, index: int):
        """
        Retreive the element with the specified index.

        Args:
          index: int: The index of the element to retrieve.

        Returns:
          The `Element <flitsr.spectrum.Spectrum.Element>` corresponding to the
          `index` given.

        Raises:
          KeyError: If the `index` does not correspond to an element.
        """
        return self._method_map[index]

    def addTest(self, name: str, outcome: Outcome, index: int = None):
        """
        Add a new test to the spectrum with the given name, index, and outcome.

        Args:
          name: The name of the test.
          index: (Default value = None) A unique identifier for this test.
          outcome: The outcome (pass/fail) of the test.
        """
        if (index is None):
            index = len(self._tests)
        t = Spectrum.Test(name, index, outcome)
        self._tests[index] = t
        self._executions[t] = set()
        return t

    def addElement(self, details: List[str],
                   faults: List[Any], index: int = None) -> Spectrum.Element:
        """
        Add a new element to the spectrum, with the given details and faults.

        Args:
          details: List[str]: The list of details of the element. The list MUST
            contain at least one string. It conforms to one of the following::

              [<name>]
              [<path>, <method>]
              [<path>, <line num>]
              [<path>, <method>, <line num>]

          faults: List[Any]: The list of faults that this element pertains to.
          index: int:  (Default value = None) The (optional) index of this
            element.

        Returns:
          The created element.
        """
        if (index is None):
            index = len(self._elements)
        i = len(self._method_map)  # number of actual elements
        if (self._collapse_methods):
            if ((details[0], details[1]) not in self._methods):
                # append with first line number
                elem = self._add_element(details, faults, index)
                self._methods[(details[0], details[1])] = elem
                self._method_map[i] = elem
            else:
                elem = self._method_map[i] = self._methods[(details[0],
                                                            details[1])]
                # update method's faults
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
        else:
            elem = self._add_element(details, faults, index)
            self._method_map[i] = elem
        return elem

    def _add_element(self, details: List[str], faults: List[Any],
                     index: int) -> Spectrum.Element:
        """
        Helper method to consistently add element to this builder.

        Args:
          details: List[str]:
          faults: List[Any]:
          index: int:

        Returns:

        """
        # Create element
        e = Spectrum.Element(details, index, faults)
        # Record element
        self._elements.append(e)
        return e

    def addExecution(self, test: Union[Spectrum.Test, int],
                     elem: Union[Spectrum.Element, int]):
        """
        Mark the specified element as executed in the given test.

        Args:
          test: Union[Spectrum.Test, int]: The test to add the execution to.
            Can be either a `Test <flitsr.spectrum.Spectrum.Test>` object OR an
            integer representing a valid index of a Test.
          elem: Union[Spectrum.Element, int]: The element to add the execution
            for. Can be either an `Element <flitsr.spectrum.Spectrum.Element>`
            object OR an integer representing a valid Element index.

        Raises:
          TestKeyError: When `test` is an int and does not refer to a valid
            test index.
          ElemKeyError: When `elem` is an int and does not refer to a valid
            element index.
        """
        # Get the test or raise execption
        if (isinstance(test, int)):
            try:
                test = self._tests[test]
            except KeyError:
                raise TestKeyError()

        # Get the element or raise execption
        if (isinstance(elem, int)):
            try:
                elem = self._method_map[elem]
            except KeyError:
                raise ElemKeyError()

        # add execution
        if (test not in self._executions):
            self._executions[test] = set()
        self._executions[test].add(elem)

    def addNonExecution(self, test: Spectrum.Test, elem: Spectrum.Element):
        """
        Mark the specified element as not executed in the given test.
        NOTE: Adding non-executions is not required for the spectrum
        (non-execution is assumed by default), thus this method does not do
        anything.

        .. deprecated:: 2.2
           There is no need to call this function anymore as non-executions are
           not stored by default.

        Args:
          test: Spectrum.Test: The Test to add the non-execution to.
          elem: Spectrum.Element: The Element to add to non-execution of.
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
        test_list = self.get_tests()
        # Initialize stack with all elements in one group
        stack.append((set(self._elements), 0))
        while (len(stack) > 0):
            cur, t_ind = stack.pop()
            if (t_ind >= len(test_list) or len(cur) == 1):
                groups.append(Spectrum.Group(list(cur)))
            else:
                test = test_list[t_ind]
                exe_elem = cur.intersection(self._executions[test])
                nexe_elem = cur.difference(exe_elem)
                if (len(exe_elem) != 0):
                    stack.append((exe_elem, t_ind+1))
                if (len(nexe_elem) != 0):
                    stack.append((nexe_elem, t_ind+1))
        return groups

    def get_spectrum(self) -> Spectrum:
        """ Return the spectrum from this `SpectrumBuilder`. """
        groups = self.form_groups()
        spectrum = Spectrum(self._elements, groups, self.get_tests(),
                            self._executions)
        return spectrum


class TestKeyError(KeyError):
    """
    Exception that is raised when a Test is not found in the `SpectrumBuilder`.
    """
    pass


class ElemKeyError(KeyError):
    """
    Exception that is raised when an Element is not found in the
    `SpectrumBuilder`.
    """
    pass


class SpectrumUpdater(SpectrumBuilder):
    """
    Allows updating of an already created spectrum using the `SpectrumBuilder`
    interface.
    """
    def __init__(self, spectrum: Spectrum):
        super().__init__(collapse_methods=False)
        self._elements = spectrum._elements[:]
        self._tests = {t.index: t for t in spectrum.tests()[:]}
        self._executions = dict()
        # copy all the executions
        for test in self.get_tests():
            new_exe = self._executions.setdefault(test, set())
            for group in spectrum.groups():
                # Only copy over actually executed elements
                if (spectrum[test][group]):
                    for elem in group:
                        new_exe.add(elem)

    def remove_test_with_executions(self, test: Spectrum.Test):
        """
        Remove the given `test` from the spectrum, including any executions
        related to it.

        Args:
          test: Spectrum.Test: The test to remove.
        """
        del self._tests[test.index]
        del self._executions[test]

    def copy_test_and_execution(self, test: Spectrum.Test, spectrum: Spectrum):
        """
        Copy over the given `test` to this spectrum, with the executions given
        in the supplied other `spectrum`.

        Args:
          test: Spectrum.Test: The test to copy over to this spectrum.
          spectrum: Spectrum: The spectrum containing the executions of `test`.
        """
        self._tests[test.index] = test
        new_exe = self._executions.setdefault(test, set())
        for group in spectrum.groups():
            # Only copy over actually executed elements
            if (spectrum[test][group]):
                for other in group:
                    # get this spectrum's element
                    elem = self._get_element(other)
                    new_exe.add(elem)

    def _get_element(self, other: Spectrum.Element) -> Spectrum.Element:
        """
        Retrieve the element from this spectrum that is semantically equal to
        the `other` element.

        Args:
          other: Spectrum.Element: The element to find a semantic equivalent
            for.

        Returns:
          The element from this spectrum that is corresponds to the `other`
            element given.

        Raises:
          KeyError: If no element could be found that is semantically equal to
            the given `other` element.
        """
        for elem in self._elements:
            if (elem.semantic_eq(other)):
                return elem
        raise KeyError(f'Could not find element {other} in SpectrumUpdater')
