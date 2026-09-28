import re
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple

from flitsr.ranking import Ranking, Rankings
from flitsr.ranking_input import RankingInput
from flitsr.spectrum import Details, Spectrum


class GzoltarRanking(RankingInput):
    """ The Gzoltar `RankingInput` type."""
    @classmethod
    def _read_ranking(cls, f: TextIO, method_level=False) -> Rankings:
        """
        Read in a GZoltar formatted ranking.
        """
        ranking = Ranking()
        bugs = 0
        methods: Dict[Tuple[str, Optional[str]], Spectrum.Element] = {}
        all_faults: Dict[Any, Set[Spectrum.Element]] = {}
        elements: List[Spectrum.Element] = []
        f.readline()
        for i, line in enumerate(f):
            line = line.strip()
            score = float(line[line.index(";")+1:])
            name = line[:line.index(";")]
            ln = name.strip().split(':')
            r = re.search("([^\\$]+)\\$([^\\$#]+)(\\$[^#]+)?#([^:]*)", ln[0])
            if (r is None):
                raise ValueError("Incorrectly formatted line \"" + line +
                                 "\" when reading input ranking file")
            faults = []
            if (len(ln) > 2):
                if (not ln[2].isdigit()):
                    faults = [bugs]
                else:
                    faults = []
                    for b in ln[2:]:
                        faults.append(int(b))
                bugs += 1
            details = Details(pname=r.group(1)+"."+r.group(2),
                              classname=r.group(3), method=r.group(4),
                              line_no=ln[1])
            # Create or fetch the element
            meth_id = (details.pname+("" if details.classname is None else
                                      "$"+details.classname), details.method)
            if (not method_level or meth_id not in methods):
                elem = Spectrum.Element(details, len(elements), faults)
                elements.append(elem)
                if (method_level):
                    methods[meth_id] = elem
            else:
                elem = methods[meth_id]
                for fault in faults:
                    if (fault not in elem.faults):
                        elem.faults.append(fault)
            # Add/Update the method's score
            if (ranking.has_entity(elem)):
                rank_elem = ranking.get_rank(elem)
                rank_elem.score = max(rank_elem.score, score)
            else:
                ranking.append(elem, score, 0)
            # Update faults
            if (elem.faults):
                for fault in elem.faults:
                    all_faults.setdefault(fault, set()).add(elem)
        return Rankings(all_faults, elements, [ranking])

    @staticmethod
    def _check_format(ranking_file: TextIO) -> bool:
        line = ranking_file.readline().strip()
        pat = "(name|Line|\\w+);([Ss]us[\\w ]*)"
        return re.fullmatch(pat, line) is not None
