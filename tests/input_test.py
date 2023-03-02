import exrex
import io
import pytest
from pytest import mark as pytestr
import input

def gen_strings(regex, num):
    return [exrex.getone(regex) for i in range(num)]

@pytestr.randomize(entries=pytest.list_of(str, min_items=1, max_items=100),
        choices=gen_strings("([a-z.]+)\$([a-z]+)#([a-z(),]+):[0-9]+(:[0-9]+)?", 1000))
def test_detail_construction(entries):
    num_entries = len(entries)
    entries = ['name'] + entries
    entries = '\n'.join(entries)
    uuts, num_locs, method_map = input.construct_details(io.StringIO(entries), False)
    assert len(uuts) == num_entries
    assert num_locs == num_entries

