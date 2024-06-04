class ConstIter:
    """
    An iterator that will return a constant value for a number of
    repetitions.
    """
    def __init__(self, rep, const=0):
        self.rep = rep
        self.const = const
        self.i = 0

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if (self.i < self.rep):
            self.i += 1
            return self.const
        else:
            raise StopIteration
