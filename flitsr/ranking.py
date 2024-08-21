import re
from typing import Tuple, List
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


def read_any_ranking(ranking_file: str,
                     method_level=False) -> Tuple[Scores, Spectrum]:
    f = open(ranking_file)
    if (f.readline().startswith("Faulty grouping")):
        return read_flitsr_ranking(ranking_file)
    else:
        return read_ranking(ranking_file, method_level)


def read_ranking(ranking_file: str,
                 method_level=False) -> Tuple[Scores, Spectrum]:
    f = open(ranking_file)
    spectrum = Spectrum()
    scores = Scores()
    i = 0  # number of actual lines
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
        if (r is None):
            raise ValueError("Incorrectly formatted line \"" + line +
                             "\" when reading input ranking file")
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
            # Add the method to the spectrum
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            if ((details[0], details[1]) not in methods):
                # add with first line number
                elem = spectrum.addElement(details, faults)
                methods[(details[0], details[1])] = elem
                method_map[i] = elem
            else:
                elem = method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
            # Add/Update the method's score
            elem = method_map[i]
            score_elem = scores[elem]
            if (score_elem is None):
                scores.append(elem, score, 0)
            else:
                score_elem.score = max(score_elem.score, score)
        else:
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            elem = spectrum.addElement(details, faults)
            method_map[i] = elem
            scores.append(elem, score, 0)
        i += 1
    # Hard-code the groups for a pre-determined spectrum
    spectrum.groups = [[elem] for elem in spectrum.elements()]
    spectrum.remove_unnecessary()
    return scores, spectrum


def read_flitsr_ranking(ranking_file: str) -> Tuple[Scores, Spectrum]:
    f = open(ranking_file)
    spectrum = Spectrum()
    scores = Scores()
    num_locs = 0  # number of reported locations (methods/lines)
    i = 0  # number of actual lines
    groups: List[List[Spectrum.Element]] = []  # manually create groups
    line = f.readline()
    while (line != ""):
        line = line.strip()
        score = float(line[line.index(": ")+2:line.index(" [")])
        line = f.readline().strip()
        groups.append([])
        while (not line.startswith("]")):
            m = re.fullmatch("\\s*(\\S*)\\s*(?:\\(FAULT ([0-9.,]+)\\))?", line)
            if (m is None):
                raise ValueError("Incorrectly formatted line \"" + line +
                                 "\" when reading input ranking file")
            details = m.group(1).split('|')
            if (m.group(2)):
                faults = [int(i) if i.isdecimal() else float(i)
                          for i in m.group(2).split(',')]
            else:
                faults = []
            elem = spectrum.addElement(details, faults)
            groups[num_locs].append(elem)
            i += 1
            line = f.readline().strip()
        scores.append(groups[num_locs][0], score, 0)
        num_locs += 1
        line = f.readline().strip()
    spectrum.groups = groups  # override groups object
    spectrum.remove_unnecessary()
    return scores, spectrum
