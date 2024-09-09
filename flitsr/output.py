import sys
from typing import Dict, List, Set
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


def print_names(spectrum, scores=None, file=sys.stdout):
    no_scores = False
    if (scores is None):  # make a tempoorary Scores object
        scores = Scores()
        for elem in spectrum.elements():
            scores.append(elem, 0, 0)
        no_scores = True
    for score in scores:
        if (no_scores):
            print("Faulty grouping: ", "[", file=file)
        else:
            print("Faulty grouping:", score.score, "[", file=file)
        group = spectrum.get_group(score.elem)
        for elem in group:
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
        if (test.outcome):
            print('+')
        else:
            print('-')


def print_csv(spectrum: Spectrum, scores: Scores, file=sys.stdout):
    print("name;suspiciousness_value", file=file)
    for score in scores:
        group = spectrum.get_group(score.elem)
        for elem in group:
            print(elem.gzoltar_str(), ';', score.score, sep='', file=file)
