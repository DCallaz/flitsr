import random
from pytest import mark as pytestr
from pytest import approx
from functools import partial
from flitsr.read_ranking import read_flitsr_ranking
from flitsr.tie import Ties, Tie
from flitsr.calculations import BUModel, exp_values
from flitsr.calculations.perms import exact_method, Calc
from flitsr.ranking import Rankings
from helper import list_strings
from io import StringIO


def create_ranking(seed: int, tie_size=10) -> Rankings:
    ranking = StringIO()
    rng = random.Random(seed)
    num_elems = rng.randint(1, 10000)
    elem_names = list_strings('u[1-9][0-9]{0,5}', num_elems)
    num_faults = rng.randint(1, max(1, min(num_elems//100, 20)))
    fault_locs = {f: rng.sample(range(0, num_elems), rng.randint(1, 10))
                  for f in range(num_faults)}
    all_fault_locs = set().union(*fault_locs.values())

    num_ties = max(num_elems//tie_size, 1)
    num_groups = rng.randint(num_ties, num_elems)
    # divide elems into groups
    # list of indices each group ends on (exclusive) in order
    group_ends = (sorted(rng.sample(range(1, num_elems), num_groups - 1))
                  + [num_elems])
    # list of suspicious scores for each tie
    sus_scores = [i/num_ties for i in range(num_ties, -1, -1)]
    # divide groups into ties
    # list of indices each tie ends on (exclusive) in order
    tie_ends = (sorted(rng.sample(range(1, num_groups), num_ties - 1))
                + [num_groups])
    start = 0
    tie_ind = 0
    for g, group in enumerate(range(num_groups)):
        if (g >= tie_ends[tie_ind]):
            tie_ind += 1
        print(f'Faulty grouping: {sus_scores[tie_ind]} [', file=ranking)
        end = group_ends[group]
        for i in range(start, end):
            # make some faults
            fault = ''
            if (i in all_fault_locs):
                faults = [str(f) for f in fault_locs if i in fault_locs[f]]
                fault = f' (FAULT {",".join(faults)})'
            print(f'  {elem_names[i]}{fault}', file=ranking)
        print(']', file=ranking)
        start = end
    ranking.seek(0)
    ret_ranking = read_flitsr_ranking(ranking)
    return ret_ranking


def _effort_sampled(tie: Tie, q: int, weffort: bool, collapse=False,
                    bu: BUModel = BUModel.PERFECT, samples=None) -> float:
    if (weffort):
        calc = Calc.WEFFORT
    else:
        calc = Calc.EXAM
    return exact_method(tie.active_fault_locations(collapse), q,
                        tie.elems(collapse, no_passive=True), calc,
                        bu=bu, samples=samples)


# @pytestr.parametrize("seed", [289218296017730])
@pytestr.parametrize("bu", [BUModel.PERFECT, BUModel.INEPT])
@pytestr.randomize(seed=int, min_num=0, max_num=int(1e15), ncalls=10)
def test_effort(bu, seed):
    rankings = create_ranking(seed, tie_size=5)
    # rankings = read_flitsr_ranking("ranking.txt")
    ties = Ties(rankings, bu)
    eff_func = partial(_effort_sampled, bu=bu, samples=10000)
    for n in range(1, len(rankings.faults())+1):
        act = exp_values.effort_exp_val(ties=ties, target=n, weffort=True)
        exp = exp_values.effort_exp_val(ties=ties, target=n, weffort=True,
                                        tie_exp_func=eff_func)
        assert act >= 0.0, f'Fault no.: {n}'
        assert act == approx(exp, rel=2e-2, abs=1e-4), f'Fault no.: {n}'


CUT_OFFS = [1, 3, 5, 10, 15, 20, 50, 100]


def _cutoff_sampled(tie: Tie, q: int, collapse=False,
                    bu: BUModel = BUModel.PERFECT, samples=None) -> float:
    return q*exact_method(tie.active_fault_locations(collapse), q,
                          tie.elems(collapse), Calc.PRECISION,
                          bu=bu, samples=samples)


@pytestr.parametrize("bu", BUModel.get_types())
@pytestr.randomize(seed=int, min_num=0, max_num=int(1e15), ncalls=10)
def test_cutoff(bu, seed):
    rankings = create_ranking(seed, tie_size=5)
    ties = Ties(rankings, bu)
    cutoff_func = partial(_cutoff_sampled, bu=bu, samples=10000)
    for n in CUT_OFFS:
        act = exp_values.cut_off_exp_val(ties=ties, target=n)
        exp = exp_values.cut_off_exp_val(ties=ties, target=n,
                                         tie_exp_func=cutoff_func)
        assert act >= 0.0, f'Target: {n}'
        assert act == approx(exp, rel=2e-2, abs=1e-2), f'Target: {n}'
