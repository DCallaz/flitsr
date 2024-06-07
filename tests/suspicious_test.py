from flitsr.suspicious import Suspicious
from pytest import mark as pytestr


@pytestr.parametrize('metric', Suspicious.getNames())
@pytestr.randomize(ef=int, nf=int, ep=int, np=int, min_num=0, max_num=10000)
def test_metrics(metric, ef, nf, ep, np):
    sus = Suspicious(ef, ef+nf, ep, ep+np)
    ans = sus.execute(metric)
    # assert ans >= 0.0
    if (ef == 0):
        assert ans <= 0.0
