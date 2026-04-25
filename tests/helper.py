import exrex


def gen_strings(regex, num):
    prev = set()
    i = 0
    while (i < num):
        entry = exrex.getone(regex, limit=100)
        if (entry not in prev):
            prev.add(entry)
            i += 1
            yield entry
