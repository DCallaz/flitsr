import sys
import os
from os import path as osp
from shutil import rmtree
from typing import Dict, List, Set
from flitsr.spectrum import Spectrum, Outcome
from flitsr.ranking import Ranking


def print_names(spectrum, ranking=None, file=sys.stdout):
    no_ranking = False
    if (ranking is None):  # make a tempoorary Scores object
        ranking = Ranking()
        for elem in spectrum.elements():
            ranking.append(elem, 0, 0)
        no_ranking = True
    for rank in ranking:
        if (no_ranking):
            print("Faulty grouping: ", "[", file=file)
        else:
            print("Faulty grouping:", rank.score, "[", file=file)
        group = rank.group
        for elem in group.get_elements():
            print(" ", elem, file=file)
        print("]", file=file)


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


def print_csv(spectrum: Spectrum, ranking: Ranking, file=sys.stdout):
    print("name;suspiciousness_value", file=file)
    for rank in ranking:
        group = rank.group
        for elem in group.get_elements():
            print(elem.gzoltar_str(), ';', rank.score, sep='', file=file)


def print_spectrum_csv(spectrum: Spectrum, file=sys.stdout):
    ts = [str(t.name)+' ('+('PASS' if t.outcome is Outcome.PASSED else
                            'FAIL')+')' for t in spectrum.tests()]
    print('Element', *ts, sep=',', file=file)
    # TODO: change _elements below to elements()
    for elem in spectrum._elements:
        # print(elem, end=',', file=file)
        tests = ['X' if spectrum[t][elem] else '' for t in spectrum.tests()]
        print(elem, *tests, sep=',', file=file)
