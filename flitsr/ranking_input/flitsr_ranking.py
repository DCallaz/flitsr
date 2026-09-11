import re
from typing import Any, Dict, List, Set, TextIO, Union

from flitsr.ranking import Ranking, Rankings
from flitsr.ranking_input import RankingInput
from flitsr.spectrum import Spectrum


class FlitsrRanking(RankingInput):
    @classmethod
    def _read_ranking(cls, f: TextIO, method_level=False) -> Rankings:
        """
        Read in a ``flitsr`` formatted ranking.
        """
        line = f.readline()
        rankings: List[Ranking] = []
        while (line != ""):
            if (re.fullmatch("<-+ Next Ranking -+>", line)):
                line = f.readline()
            ranking = Ranking()
            rankings.append(ranking)
            all_faults: Dict[Any, Set[Spectrum.Element]] = {}
            elements: List[Spectrum.Element] = []
            num_locs = 0  # number of reported locations (methods/lines)
            i = 0  # number of actual lines
            while (line != "" and "Next Ranking" not in line):
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
                    elem_pat = ("\\s*(?:\\([0-9]+\\)\\s*)?(\\S*)\\s*"  # detail
                                "(?:\\(FAULT ([0-9.,]+)\\))?")         # fault
                    m = re.fullmatch(elem_pat, line)
                    if (m is None):
                        # if normal format fails, try DUA format
                        dua_pat = ("\\s*(?:\\([0-9]+\\)\\s*)?"     # old format
                                   "(\\S*\\s\\S*\\s\\S*)\\s*"      # detail
                                   "(?:\\(FAULT ([0-9.,]+)\\))?")  # fault
                        m = re.fullmatch(dua_pat, line)
                        if (m is None):
                            raise ValueError("Incorrectly formatted line "
                                             f"\"{line}\" when reading input "
                                             "ranking file")
                    details = m.group(1).split('|')
                    if (m.group(2)):
                        faults = [int(i) if i.isdecimal() else float(i)
                                  for i in m.group(2).split(',')]
                    else:
                        faults = []
                    elem = Spectrum.Element(details, len(elements), faults)
                    elements.append(elem)
                    for fault in faults:
                        all_faults.setdefault(fault, set()).add(elem)
                    group_elems.append(elem)
                    i += 1
                    line = f.readline().strip()
                group = Spectrum.Group(group_elems)
                ranking.append(group, score, 0)
                num_locs += 1
                line = f.readline().strip()
        ret_rankings = Rankings(all_faults, elements, rankings)
        return ret_rankings

    @staticmethod
    def _check_format(ranking_file: TextIO) -> bool:
        line = ranking_file.readline().strip()
        return line.startswith("Faulty grouping")
