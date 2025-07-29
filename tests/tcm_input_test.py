import io
import pytest
import random
from pytest import mark as pytestr
from helper import gen_strings
from flitsr.input.tcm_input import TCM
from flitsr.spectrumBuilder import SpectrumBuilder
from flitsr.spectrum import Outcome

@pytestr.randomize(entries=pytest.list_of(str, min_items=1, max_items=100),
                   choices=gen_strings("([a-z.]+).([a-z]+):([a-z(),]+)"
                                       ":[0-9]+( \\| [0-9]+)?", 1000),
                   ncalls=20)
def test_detail_construction(entries):
    inp = TCM()
    entries = set(entries)
    num_entries = len(entries)
    entries = '\n'.join(entries) + "\n\n"
    sb = SpectrumBuilder()
    inp.construct_details(io.StringIO(entries), False, sb)
    assert num_entries == len(sb._elements)


@pytestr.randomize(entries=pytest.list_of(str, min_items=1, max_items=100),
                   choices=gen_strings("([a-z.]+) (PASSED|FAILED)", 1000),
                   ncalls=20)
def test_test_construction(entries):
    inp = TCM()
    entries = set(entries)
    num_entries = len(entries)
    entries = '\n'.join(entries) + "\n\n"
    sb = SpectrumBuilder()
    inp.construct_tests(io.StringIO(entries), sb)
    assert num_entries == len(sb._tests)


@pytestr.randomize(num_tests=int, num_elems=int, ncalls=10, max_num=500,
                   min_num=1)
def test_fill_spectrum(num_tests, num_elems):
    # Constructing spectrum
    inp = TCM()
    sb = SpectrumBuilder()
    # Filling elements
    method_map = {}
    elem_names = gen_strings("[a-z.]+", num_elems)
    elem_faults = [[random.randint(0, 100)
                    for _ in range(random.randint(0, 3) % 3)]
                   for _ in range(num_elems)]
    for i in range(num_elems):
        elem = sb.addElement([elem_names[i]], elem_faults[i])
        method_map[i] = elem
    # Filling tests
    test_names = gen_strings("[a-z.]+", num_tests)
    test_outcomes = [Outcome(random.randint(0, 1)) for _ in range(num_tests)]
    print(test_outcomes)
    for i in range(num_tests):
        sb.addTest(test_names[i], test_outcomes[i], index=i)
    matrix = ""
    elem_list = [i for i in range(num_elems)]
    for t in range(num_tests):
        execs = random.sample(elem_list, random.randint(0, num_elems))
        for e in execs:
            matrix += str(e) + " 1 "
        matrix += "\n"
    inp.fill_spectrum(io.StringIO(matrix), sb)
    spectrum = sb.get_spectrum()
    num_failed = len([t for t in test_outcomes if t is Outcome.FAILED])
    num_passed = len([t for t in test_outcomes if t is Outcome.PASSED])
    assert len(spectrum.failing()) == num_failed
    assert spectrum.tf == num_failed
    assert spectrum.tp == num_passed
