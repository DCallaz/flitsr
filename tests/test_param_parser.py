import importlib
from importlib.resources import files
import pytest
from pytest import mark as pytestr
from resources import parameter_parser_routines as pp_routines
from flitsr.args import ParameterParser


def test_function():
    pp = ParameterParser(pp_routines.test)
    assert pp.ismethod is False
    assert pp.name == 'test'
    assert pp._def_diff == 2
    param1, parser_args_p1 = next(pp)
    assert param1 == 'i'
    assert parser_args_p1['required'] is True
    assert parser_args_p1['metavar'] == 'i'
    assert parser_args_p1['type'] == int
    param2, parser_args_p2 = next(pp)
    assert param2 == 's'
    assert parser_args_p2['required'] is True
    assert parser_args_p2['metavar'] == 's'
    assert parser_args_p2['type'] == str
    assert parser_args_p2['choices'] == ['a', 'b']


@pytestr.parametrize('fn,cls', [(pp_routines.P.test2, pp_routines.P),
                                (object.__new__(pp_routines.P).test2, None)],
                     ids=['with_class', 'without_class'])
def test_instance_method(fn, cls):
    pp = ParameterParser(fn, class_=cls)
    assert pp.ismethod is True
    assert pp.name == 'test2'
    assert pp._def_diff == 1
    param1, parser_args_p1 = next(pp)
    assert param1 == 'i'
    assert parser_args_p1['required'] is True
    assert parser_args_p1['metavar'] == 'i'
    assert parser_args_p1['type'] == int
    param2, parser_args_p2 = next(pp)
    assert param2 == 's'
    assert parser_args_p2['metavar'] == 's'
    assert parser_args_p2['type'] == str
    assert parser_args_p2['default'] == 's'


@pytestr.parametrize('fn,cls', [(pp_routines.P.test3, pp_routines.P),
                                (object.__new__(pp_routines.P).test3, None)],
                     ids=['with_class', 'without_class'])
def test_static_method(fn, cls):
    pp = ParameterParser(fn, class_=cls)
    assert pp.ismethod is False
    assert pp.name == 'test3'
    assert pp._def_diff == 2
    param1, parser_args_p1 = next(pp)
    assert param1 == 'i'
    assert parser_args_p1['required'] is True
    assert parser_args_p1['metavar'] == 'i'
    assert parser_args_p1['type'] == int
    param2, parser_args_p2 = next(pp)
    assert param2 == 's'
    assert parser_args_p2['required'] is True
    assert parser_args_p2['metavar'] == 's'
    assert parser_args_p2['type'] == str
    assert parser_args_p2['choices'] == ['a', 'b']


@pytestr.parametrize('fn,cls', [(pp_routines.P.test4, pp_routines.P),
                                (object.__new__(pp_routines.P).test4, None)],
                     ids=['with_class', 'without_class'])
def test_class_method(fn, cls):
    pp = ParameterParser(fn, class_=cls)
    assert pp.ismethod is True
    assert pp.name == 'test4'
    assert pp._def_diff == 2
    param1, parser_args_p1 = next(pp)
    assert param1 == 'i'
    assert parser_args_p1['required'] is True
    assert parser_args_p1['metavar'] == 'i'
    assert parser_args_p1['type'] == int
    param2, parser_args_p2 = next(pp)
    assert param2 == 's'
    assert parser_args_p2['metavar'] == 's'
    assert parser_args_p2['type'] == str
    assert parser_args_p2['required'] is True
