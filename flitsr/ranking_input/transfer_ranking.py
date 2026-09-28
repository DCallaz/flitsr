import re
from typing import Any, Dict, List, Set, TextIO

from flitsr.ranking import Ranking, Rankings
from flitsr.ranking_input import RankingInput
from flitsr.spectrum import Spectrum


class TransferFLRanking(RankingInput):
    """ The Transfer-FL `RankingInput` type."""
    @classmethod
    def _read_ranking(cls, f: TextIO, method_level=False) -> Rankings:
        """
        Read in a TRANSFER-FL formatted ranking.
        """
        ranking = Ranking()
        all_faults: Dict[Any, Set[Spectrum.Element]] = {}
        elements: List[Spectrum.Element] = []
        for _, line in enumerate(f):
            line = line.strip()
            ln = line.split()
            score = float(ln[1])
            name = ln[0]
            faults = []
            if (len(ln) > 2):
                for b in ln[2:]:
                    faults.append(int(b))
            details = name.split('@')
            # Create the element
            elem = Spectrum.Element(details, len(elements), faults)
            elements.append(elem)
            for fault in faults:
                all_faults.setdefault(fault, set()).add(elem)

            # Add/Update the method's score
            ranking.append(elem, score, 0)
        return Rankings(all_faults, elements, [ranking])

    @staticmethod
    def _check_format(ranking_file: TextIO) -> bool:
        line = ranking_file.readline().strip()
        return re.fullmatch("[\\w.]+@[0-9]+\\s+[0-9.]+(\\s+[0-9]+)?",
                            line) is not None
