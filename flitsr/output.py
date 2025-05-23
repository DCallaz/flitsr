import sys
import os
from os import path as osp
from shutil import rmtree
from typing import Dict, List, Set
from flitsr.spectrum import Spectrum, Outcome
from flitsr.ranking import Ranking
from flitsr.input_type import InputType


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


def print_tcm(spectrum: Spectrum, file=sys.stdout):
    """ Output the spectrum in TCM format """
    print("#tests", file=file)
    for test in spectrum.tests():
        print(test.name, test.outcome.name, file=file)
    print(file=file)
    print("#uuts", file=file)
    # TODO: change _elements below to elements()
    for elem in spectrum._elements:
        print(elem.output_str(type_=InputType.TCM), file=file)
    print(file=file)
    print("#matrix", file=file)
    for test in spectrum.tests():
        first = True
        for elem_id, elem in enumerate(spectrum._elements):
            if (spectrum[test][elem]):
                print(("" if first else " ")+str(elem_id), "1", end="",
                      file=file)
                first = False
        print(file=file)


def print_gzoltar(spectrum: Spectrum, directory: str):
    """ Output the spectrum in Gzoltar format """
    # First check that the directory exists and is empty
    if (not osp.isdir(directory)):
        os.mkdir(directory)
    else:
        rmtree(directory)
        os.mkdir(directory)
    # Next print out the tests
    with open(osp.join(directory, "tests.csv"), 'w') as test_file:
        print("name,outcome,runtime,stacktrace", file=test_file)
        for test in spectrum.tests():
            print(test.name, "PASS" if test.outcome is Outcome.PASSED else
                  "FAIL", "", "", sep=",", file=test_file)
    with open(osp.join(directory, "spectra.csv"), 'w') as units_file:
        print("name", file=units_file)
        # TODO: change _elements below to elements()
        for elem in spectrum._elements:
            print(elem.output_str(type_=InputType.GZOLTAR), file=units_file)
    with open(osp.join(directory, "matrix.txt"), 'w') as matrix_file:
        for test in spectrum.tests():
            for elem in spectrum._elements:
                print(int(spectrum[test][elem]), end=" ", file=matrix_file)
            print('+' if test.outcome is Outcome.PASS else '-',
                  file=matrix_file)
