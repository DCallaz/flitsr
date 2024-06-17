from typing import Union
from os import DirEntry

class File:
    def __init__(self, file: Union[str, DirEntry]):
        fopen = open(file)
        self.lines = fopen.readlines()
        fopen.close()
        self.i = 0

    def readline(self) -> str:
        if (self.i < len(self.lines)):
            self.i += 1
            return self.lines[self.i-1]
        return ''

    def hasline(self) -> bool:
        return self.i < len(self.lines)
