import re
from typing import Tuple, List, Union, Any
from flitsr.spectrum import Spectrum
from flitsr.ranking import Ranking


class RankingSpectrumBuilder:
    def __init__(self):
        self._elements: List[Spectrum.Element] = []
        self._groups: List[Spectrum.Group] = []

    def addElement(self, details: List[str],
                   faults: List[Any]) -> Spectrum.Element:
        e = Spectrum.Element(details, len(self._elements), faults)
        self._elements.append(e)
        return e

    def createGroup(self, elems: List[Spectrum.Element]) -> Spectrum.Group:
        """
        Hard-code the groups for a pre-determined spectrum
        """
        i = len(self._groups)
        g = Spectrum.Group(elems, i)
        self._groups.append(g)
        for e in elems:
            e.set_group(g)
        return g

    def get_spectrum(self):
        return Spectrum(self._elements, self._groups, [], {})


def read_any_ranking(ranking_file: str,
                     method_level=False) -> Tuple[Ranking, Spectrum]:
    f = open(ranking_file)
    if (f.readline().startswith("Faulty grouping")):
        return read_flitsr_ranking(ranking_file)
    else:
        return read_ranking(ranking_file, method_level)


def read_ranking(ranking_file: str,
                 method_level=False) -> Tuple[Ranking, Spectrum]:
    f = open(ranking_file)
    spectrumBuilder = RankingSpectrumBuilder()
    ranking = Ranking()
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
        r = re.search("(.*)\\$(.*)#([^:]*)", l[0])
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
                elem = spectrumBuilder.addElement(details, faults)
                spectrumBuilder.createGroup([elem])
                methods[(details[0], details[1])] = elem
                method_map[i] = elem
            else:
                elem = method_map[i] = methods[(details[0], details[1])]
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
            # Add/Update the method's score
            elem = method_map[i]
            group = elem.group()
            if (ranking.has_group(group)):
                rank_elem = ranking.get_rank(group)
                rank_elem.score = max(rank_elem.score, score)
            else:
                ranking.append(group, score, 0)
        else:
            details = [r.group(1)+"."+r.group(2), r.group(3), l[1]]
            elem = spectrumBuilder.addElement(details, faults)
            spectrumBuilder.createGroup([elem])
            method_map[i] = elem
            ranking.append(elem.group(), score, 0)
        i += 1
    spectrum = spectrumBuilder.get_spectrum()
    return ranking, spectrum


def read_flitsr_ranking(ranking_file: str) -> Tuple[Ranking, Spectrum]:
    f = open(ranking_file)
    spectrumBuilder = RankingSpectrumBuilder()
    ranking = Ranking()
    num_locs = 0  # number of reported locations (methods/lines)
    i = 0  # number of actual lines
    line = f.readline()
    while (line != ""):
        line = line.strip()
        score: Union[int, float]
        str_score = line[line.index(": ")+2:line.index(" [")]
        if (str_score.isdigit()):
            score = int(str_score)
        else:
            score = float(str_score)
        line = f.readline().strip()
        group_elems = []
        while (not line.startswith("]")):
            # read in ranked element (old or new FLITSR format)
            m = re.fullmatch("\\s*(?:\\([0-9]+\\)\\s*)?(\\S*)\\s*(?:\\(FAULT ([0-9.,]+)\\))?", line)
            if (m is None):
                # if normal format fails, try DUA format
                m = re.fullmatch("\\s*(?:\\([0-9]+\\)\\s*)?(\\S*\\s\\S*\\s\\S*)\\s*(?:\\(FAULT ([0-9.,]+)\\))?", line)
                if (m is None):
                    raise ValueError("Incorrectly formatted line \"" + line +
                                     "\" when reading input ranking file")
            details = m.group(1).split('|')
            if (m.group(2)):
                faults = [int(i) if i.isdecimal() else float(i)
                          for i in m.group(2).split(',')]
            else:
                faults = []
            elem = spectrumBuilder.addElement(details, faults)
            group_elems.append(elem)
            i += 1
            line = f.readline().strip()
        group = spectrumBuilder.createGroup(group_elems)
        ranking.append(group, score, 0)
        num_locs += 1
        line = f.readline().strip()
    spectrum = spectrumBuilder.get_spectrum()
    return ranking, spectrum
