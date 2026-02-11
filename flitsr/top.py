from flitsr.tie import Ties, Tie
from flitsr.precision_recall import method


def one_top_n(ties: Ties, n: int, collapse=False) -> float:
    k, _ = method(n, ties, collapse=collapse)
    return min(1.0, k)


def all_top_n(ties: Ties, n: int, collapse=False) -> float:
    k, _ = method(n, ties, collapse=collapse)
    return k


def perc_top_n(ties: Ties, n: int, collapse=False) -> float:
    if (len(ties.faults) == 0):
        return 100
    else:
        k, _ = method(n, ties, collapse=collapse)
        return (k/len(ties.faults))*100


def size_top1(ties: Ties) -> int:
    tie = get_top1(ties)
    return len(tie.elems())


# <------------------------- Helper functions ---------------------->


def get_top1(ties: Ties) -> Tie:
    tie_iter = iter(ties)
    return next(tie_iter)
