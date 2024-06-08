import exrex

def gen_strings(regex, num):
    ret = set()
    i = 0
    while(i < num):
        entry = exrex.getone(regex, limit=100)
        if (entry not in ret):
            ret.add(entry)
            i += 1
        else:
            print(entry, "already in list")
    return list(ret)
