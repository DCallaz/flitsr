import sys
from typing import List, Optional
from flitsr.spectrum import Spectrum, Outcome
from flitsr.ranking import Ranking, Rankings
from flitsr.input import InputType


def print_flitsr_ranking(ranking: Optional[Ranking],
                         elems: List[Spectrum.Element], file=sys.stdout):
    no_ranking = False
    if (ranking is None):  # make a tempoorary Scores object
        ranking = Ranking()
        for elem in elems:
            ranking.append(elem, 0, 0)
        no_ranking = True
    for rank in ranking:
        if (no_ranking):
            print("Faulty grouping: ", "[", file=file)
        else:
            print("Faulty grouping:", rank.score, "[", file=file)
        entity = rank.entity
        for elem in entity:
            print(" ", elem, file=file)
        print("]", file=file)


def print_rankings(rankings: Rankings, csv=False, file=sys.stdout):
    for (i, ranking) in enumerate(rankings):
        if (i > 0):
            print('<', '-'*22, ' Next Ranking ', '-'*22, '>', sep='',
                  file=file)
        if (csv):
            print_csv_ranking(ranking, file=file)
        else:
            print_flitsr_ranking(ranking, rankings.elements(), file=file)


# TODO: this function does not produce nice looking output
def print_spectrum(spectrum: Spectrum):
    for test in spectrum.tests():
        print(test.name, end=": ")
        row = spectrum[test]
        for elem in row:
            if (row[elem]):
                print(elem, end=" ")
        if (test.outcome is Outcome.PASSED):
            print('+')
        else:
            print('-')


def print_csv_ranking(ranking: Ranking, file=sys.stdout):
    print("name;suspiciousness_value", file=file)
    for rank in ranking:
        entity = rank.entity
        for elem in entity:
            print(elem.output_str(type_=InputType['GZOLTAR']),
                  ';', rank.score, sep='', file=file)


def print_spectrum_csv(spectrum: Spectrum, file=sys.stdout):
    ts = [str(t.name)+' ('+('PASS' if t.outcome is Outcome.PASSED else
                            'FAIL')+')' for t in spectrum.tests()]
    print('Element', *ts, sep=',', file=file)
    # TODO: change _elements below to elements()
    for elem in spectrum._elements:
        # print(elem, end=',', file=file)
        tests = ['X' if spectrum[t][elem] else '' for t in spectrum.tests()]
        print(elem, *tests, sep=',', file=file)
