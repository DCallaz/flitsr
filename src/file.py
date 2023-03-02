class File:
    def __init__(self, file):
        fopen = open(file)
        self.lines = fopen.readlines()
        fopen.close()
        self.i = 0

    def readline(self):
        if (self.i < len(self.lines)):
            self.i += 1
            return self.lines[self.i-1]
        return ''
