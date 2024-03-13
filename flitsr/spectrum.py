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
            self.spectra = dict()

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

    class Execution():
        """
        The Execution object holds all of the spectral information pertaining
        to the execution of a particular test.
        """
        def __init__(self):
            self.elements = []

    def __init__(self):
        self.spectrum = {}
        self.tests = []

    def __getitem__(self, t: Test):
        return self.spectrum[t]

    def __iter__(self):
        return self.tests.__iter__()

    def __next__(self):
        return self.tests.__next__()

    def addTest(self, name: str, outcome: bool):
        t = self.Test(name, outcome)
        self.tests.append(t)

    def addExecution(self, test_index: int, row: Execution):
        test = self.tests[test_index]
        self.spectrum[test] = row
