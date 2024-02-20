import re


def read_any_ranking(ranking_file, method_level=False):
    f = open(ranking_file)
    if (f.readline().startswith("Faulty grouping")):
        return read_flitsr_ranking(ranking_file)
    else:
        return read_ranking(ranking_file, method_level)


def read_ranking(ranking_file, method_level=False):
    f = open(ranking_file)
    num_locs = 0 # number of reported locations (methods/lines)
    i = 0 # number of actual lines
    uuts = []
    sort = []
    bugs = 0
    method_map = {}
    methods = {}
    f.readline()
    for line in f:
        line = line.strip()
        score = float(line[line.index(";")+1:])
        name = line[:line.index(";")]
        l = name.strip().split(':')
        r = re.search("(.*)\$(.*)#([^:]*)", l[0])
        faults = []
        if (len(l) > 2):
            if (not l[2].isdigit()):
                faults = [bugs]
            else:
                faults = []
                for b in l[2:]:
                    faults.append(int(b))
            bugs += 1
        if (method_level):
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            if ((details[0], details[1]) not in methods):
                methods[(details[0], details[1])] = num_locs
                method_map[i] = num_locs
                uuts.append((details, faults)) # append with first line number
                num_locs += 1
            else:
                method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in uuts[method_map[i]][1]):
                        uuts[method_map[i]][1].append(fault)
                #uuts[method_map[i]][1].extend(faults)
            ix = method_map[i]
            if (ix >= len(sort)):
                sort.append([score, ix, 0])
            else:
                sort[ix][0] = max(sort[ix][0], score)
        else:
            method_map[i] = i
            uuts.append(([r.group(1)+"."+r.group(2), r.group(3), l[1]], faults))
            sort.append([score, i, 0])
            num_locs += 1
        i += 1
    groups = [[i] for i in range(0, num_locs)]
    return sort,uuts,groups

def read_flitsr_ranking(ranking_file):
    f = open(ranking_file)
    num_locs = 0  # number of reported locations (methods/lines)
    i = 0  # number of actual lines
    uuts = []
    sort = []
    groups = []
    line = f.readline()
    while (line != ""):
        line = line.strip()
        score = float(line[line.index(": ")+2:line.index(" [")])
        line = f.readline().strip()
        groups.append([])
        while (not line.startswith("]")):
            m = re.fullmatch("\s*\([0-9]+\) (\S*)\s*(?:\(FAULT ([0-9,]+)\))?", line)
            details = m.group(1).split('|')
            faults = m.group(2).split(',') if m.group(2) else []
            uuts.append((details, faults))
            groups[num_locs].append(i)
            i += 1
            line = f.readline().strip()
        sort.append([score, num_locs, 0])
        num_locs += 1
        line = f.readline().strip()
    return sort, uuts, groups
