import random
from pytest import mark as pytestr
from pytest import approx
from flitsr.read_ranking import read_flitsr_ranking
from flitsr.tie import Ties
from flitsr.calculations import BUModel, weffort
from flitsr.ranking import Rankings
from helper import list_strings
from io import StringIO


def create_ranking(seed: int) -> Rankings:
    ranking = StringIO()
    rng = random.Random(seed)
    num_elems = rng.randint(1, 10000)
    elem_names = list_strings('u[1-9][0-9]{0,5}', num_elems)
    num_groups = rng.randint(1, 100)
    num_faults = rng.randint(1, max(1, min(num_elems//100, 20)))
    fault_locs = {f: rng.sample(range(0, num_elems), rng.randint(1, 10))
                  for f in range(num_faults)}
    all_fault_locs = set().union(*fault_locs.values())
    # print(num_elems, num_groups, num_faults, fault_locs)
    lengths = (sorted(rng.sample(range(0, num_elems), num_groups - 1)) +
               [num_elems-1])
    num_sus_scores = rng.randint(1, num_groups)
    sus_scores = [i/num_sus_scores for i in range(num_sus_scores, -1, -1)]
    sus_lengths = (sorted(rng.sample(range(0, num_groups), num_sus_scores))
                   + [num_groups-1])
    # print(len(sus_scores), len(sus_lengths), sus_lengths, sus_scores)
    start = 0
    sus_ind = 0
    for g, group in enumerate(range(num_groups)):
        if (g > sus_lengths[sus_ind]):
            sus_ind += 1
        print(f'Faulty grouping: {sus_scores[sus_ind]} [', file=ranking)
        end = lengths[group]
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


@pytestr.parametrize("bu", [BUModel.PERFECT, BUModel.INEPT])
@pytestr.randomize(seed=int, min_num=0, max_num=int(1e15), ncalls=20)
def test_weffort(bu, seed):
    rankings = create_ranking(seed)
    ties = Ties(rankings, bu)
    for n in range(1, len(rankings.faults())+1):
        weff = weffort.nth(ties=ties, collapse=False, n=n)
        smpl = weffort.partial_sampled(ties=ties, collapse=False, n=n,
                                       samples=10000)
        assert weff >= 0.0, f'Fault no.: {n}'
        assert weff == approx(smpl, rel=2e-2, abs=1e-4), f'Fault no.: {n}'
