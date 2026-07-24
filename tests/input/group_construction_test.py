from flitsr.input import Input
import pytest
from tests import resources
from importlib.resources import files
import numpy as np
from numpy.testing import assert_array_equal


@pytest.fixture
def spectrum_matrix():
    return (np.array([[True, True, True, True, True, False, False, False,
                       False, False, True, False, False, False, False, False,
                       False, False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, False,
                       True, False, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, True, True, False, True, False,
                       True, False, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, True, False,
                       True, False, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, False, False,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, False, False,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, False, False,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, True, False, False,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [True, True, True, True, False, True, False, True, True,
                       False, True, False, False, False, False, False, False,
                       False, False],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, True,
                       False, False, False],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, False,
                       True, False, True],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, False,
                       False, False, False],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, False,
                       True, False, True],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, True,
                       False, False, False],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, False,
                       True, False, True],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, False, True, True, False,
                       True, False, True],
                      [False, False, False, False, False, False, False, False,
                       False, False, False, True, True, False, False, False,
                       False, False, False],
                      [True, True, True, True, False, True, True, True, True,
                       False, True, True, False, True, True, False, True, True,
                       False],
                      [True, True, True, True, True, False, False, False,
                       False, False, True, True, False, True, True, True,
                       False, False, False],
                      [True, True, True, True, True, False, False, False,
                       False, False, True, True, False, True, True, True,
                       False, False, False]]),
            np.array([True, True, True, True, True, False, False,
                      False, False, False, False, False, False,
                      False, False, True, True, True, False,
                      False, False, False, False, False, False, False]))


@pytest.fixture
def inp_file():
    return files(resources).joinpath("input").joinpath("motiv.tcm")


# <----------------------- Unit Tests -------------------->

def test_default_groups_unit(inp_file, spectrum_matrix):
    spectrum = Input.read_in(inp_file)
    assert spectrum.locs() == 5
    group_ids = []
    for group in spectrum.groups():
        elem_ids = set([elem.index() for elem in group])
        group_ids.append(elem_ids)
    assert group_ids == [{0, 1, 2, 3}, {4, 5, 6, 7}, {8, 9, 10, 11},
                         {12, 13, 14, 15}, {16, 17, 18}]


def test_constructed_groups_unit(inp_file, spectrum_matrix):
    spectrum = Input.read_in(inp_file, compute_groups=True)
    assert spectrum.locs() == 15
    group_ids = []
    for group in spectrum.groups():
        elem_ids = set([elem.index() for elem in group])
        group_ids.append(elem_ids)
    assert group_ids == [{0, 1, 2, 3}, {4}, {5}, {6}, {7}, {8}, {9}, {10},
                         {11}, {12}, {13, 14}, {15}, {16}, {17}, {18}]
    new_matrix = []
    sorted_elems = sorted(spectrum.elements(), key=lambda x: x.index())
    for test in sorted(spectrum.tests(), key=lambda x: x.index):
        matrix_row = [spectrum[test][elem] for elem in sorted_elems]
        new_matrix.append(matrix_row)
    assert_array_equal(np.array(new_matrix), spectrum_matrix[0])


def test_non_constructed_groups_unit(inp_file, spectrum_matrix):
    spectrum = Input.read_in(inp_file, compute_groups=False)
    assert spectrum.locs() == 19
    group_ids = []
    for group in spectrum.groups():
        elem_ids = set([elem.index() for elem in group])
        group_ids.append(elem_ids)
    assert group_ids == [{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9},
                         {10}, {11}, {12}, {13}, {14}, {15}, {16}, {17}, {18}]
    new_matrix = []
    sorted_elems = sorted(spectrum.elements(), key=lambda x: x.index())
    for test in sorted(spectrum.tests(), key=lambda x: x.index):
        matrix_row = [spectrum[test][elem] for elem in sorted_elems]
        new_matrix.append(matrix_row)
    assert_array_equal(np.array(new_matrix), spectrum_matrix[0])
