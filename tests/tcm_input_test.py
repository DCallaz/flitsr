import io
import pytest
import random
from pytest import mark as pytestr
from helper import gen_strings
from flitsr.tcm_input import construct_details, construct_tests, fill_table
from flitsr.spectrum import Spectrum

@pytestr.randomize(entries=pytest.list_of(str, min_items=1, max_items=100),
        choices=gen_strings("([a-z.]+).([a-z]+):([a-z(),]+):[0-9]+( \\| [0-9]+)?",
                            1000), ncalls=20)
def test_detail_construction(entries):
    entries = set(entries)
    num_entries = len(entries)
    entries = '\n'.join(entries) + "\n\n"
    spectrum = Spectrum()
    method_map = construct_details(io.StringIO(entries), False, spectrum)
    assert num_entries == len(spectrum.elements)

@pytestr.randomize(entries=pytest.list_of(str, min_items=1, max_items=100),
        choices=gen_strings("([a-z.]+) (PASSED|FAILED)", 1000), ncalls=20)
def test_test_construction(entries):
    entries = set(entries)
    num_entries = len(entries)
    entries = '\n'.join(entries) + "\n\n"
    spectrum = Spectrum()
    method_map = construct_tests(io.StringIO(entries), spectrum)
    assert num_entries == len(spectrum.tests)

@pytestr.randomize(num_tests=int, num_elems=int, ncalls=10, max_num=500,
                   min_num=1)
def test_fill_table(num_tests, num_elems):
    # Constructing spectrum
    spectrum = Spectrum()
    # Filling elements
    method_map = {}
    elem_names = gen_strings("[a-z.]+", num_elems)
    elem_faults = [[random.randint(0, 100) for _ in range(random.randint(0, 3)%3)]
                                           for _ in range(num_elems)]
    for i in range(num_elems):
        elem = spectrum.addElement([elem_names[i]], elem_faults[i])
        method_map[i] = elem
    # Filling tests
    test_names = gen_strings("[a-z.]+", num_tests)
    test_outcomes = [bool(random.randint(0, 1)) for _ in range(num_tests)]
    for i in range(num_tests):
        spectrum.addTest(test_names[i], test_outcomes[i])
    matrix = ""
    elem_list = [i for i in range(num_elems)]
    for t in range(num_tests):
        execs = random.sample(elem_list, random.randint(0, num_elems))
        for e in execs:
            matrix += str(e) + " 1 "
        matrix += "\n"
    fill_table(io.StringIO(matrix), method_map, spectrum)
    assert len(spectrum.failing) == len([t for t in test_outcomes if t == 0])
    assert spectrum.tf == len([t for t in test_outcomes if t == 0])
    assert spectrum.tp == len([t for t in test_outcomes if t == 1])
