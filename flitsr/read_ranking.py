import re
from typing import Tuple, List, Set, Union, Any, Dict, TextIO, Optional
from flitsr.spectrum import Spectrum, Details
from flitsr.ranking import Ranking, Rankings
from flitsr.errors import error


def read_any_ranking(ranking_file: Union[str, TextIO],
                     method_level=False) -> Rankings:
    """
    Guess the ranking from the contents of the `ranking_file` and read it in.
    Closes the file after reading (even if an open file handle is given).

    Args:
      ranking_file: str: The ranking input file to read in.
      method_level:  (Default value = False) Whether the ranking file is method
        level.

    Returns:
      A `Rankings <flitsr.ranking.Rankings>` object containing the single
      read-in ranking.
    """
    with (open(ranking_file) if isinstance(ranking_file, str)
          else ranking_file) as f:
        line = f.readline().strip()
        f.seek(0)
        try:
            if (line.startswith("Faulty grouping")):
                return read_flitsr_ranking(f)
            elif (re.fullmatch("(name|Line|\\w+);([Ss]us[\\w ]*)", line)):
                return read_gzoltar_ranking(f, method_level)
            elif (re.fullmatch("[\\w.]+@[0-9]+\\s+[0-9.]+", line)):
                return read_transfer_ranking(ranking_file)
            else:
                error(f"Unrecognized ranking format for file: {ranking_file}")
        except Exception as e:
            error(f"{type(e).__name__} exception occurred while reading in "
                  f"ranking \"{ranking_file}\": {e}")


def read_transfer_ranking(ranking_file: Union[str, TextIO]) -> Rankings:
    """
    Read in a TRANSFER-FL formatted ranking.
    """
    if (isinstance(ranking_file, str)):
        f: TextIO = open(ranking_file)
    else:
        f = ranking_file
    ranking = Ranking()
    all_faults: Dict[Any, Set[Spectrum.Element]] = {}
    elements: List[Spectrum.Element] = []
    for _, line in enumerate(f):
        line = line.strip()
        l = line.split()
        score = float(l[1])
        name = l[0]
        faults = []
        if (len(l) > 2):
            for b in l[2:]:
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


def read_gzoltar_ranking(ranking_file: Union[str, TextIO],
                         method_level=False) -> Rankings:
    """
    Read in a GZoltar formatted ranking.
    """
    if (isinstance(ranking_file, str)):
        f: TextIO = open(ranking_file)
    else:
        f = ranking_file
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
        l = name.strip().split(':')
        r = re.search("([^\\$]+)\\$([^\\$#]+)(\\$[^#]+)?#([^:]*)", l[0])
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
        details = Details(pname=r.group(1)+"."+r.group(2),
                          classname=r.group(3), method=r.group(4),
                          line_no=l[1])
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


def read_flitsr_ranking(ranking_file: Union[str, TextIO]) -> Rankings:
    """
    Read in a ``flitsr`` formatted ranking.
    """
    if (isinstance(ranking_file, str)):
        f: TextIO = open(ranking_file)
    else:
        f = ranking_file
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
                m = re.fullmatch("\\s*(?:\\([0-9]+\\)\\s*)?(\\S*)\\s*(?:\\(FAULT ([0-9.,]+)\\))?", line)
                if (m is None):
                    # if normal format fails, try DUA format
                    m = re.fullmatch("\\s*(?:\\([0-9]+\\)\\s*)?(\\S*\\s\\S*\\s\\S*)\\s*(?:\\(FAULT ([0-9.,]+)\\))?", line)
                    if (m is None):
                        raise ValueError(f"Incorrectly formatted line \"{line}"
                                         "\" when reading input ranking file")
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
