import exrex
from typing import List
from collections.abc import Generator


def gen_strings(regex, num) -> Generator[str]:
    prev = set()
    i = 0
    while (i < num):
        entry = exrex.getone(regex, limit=100)
        if (entry not in prev):
            prev.add(entry)
            i += 1
            yield entry


def list_strings(regex, num) -> List[str]:
    return list(gen_strings(regex, num))
