from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation
from flitsr.calculations.exp_values import effort_exp_val
from flitsr.calculations.bu_model import BUModel
from flitsr.errors import warning
from math import nan


def mfr_print_name(ties: Ties, collapse: bool, n: int):
    return f"mean first rank ({n})"


@calculation(mfr_print_name, 'Display the mean first rank (MFR) to the nth '
             'fault', 'mfr', 'mean-first-rank')
def mfr(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    ties.set_bug_understanding(BUModel.PERFECT)
    return effort_exp_val(ties, n, weffort=False, collapse=collapse)


@calculation('mean average rank', 'Display the mean average rank (MAR) to the '
             '(first) fault. Only valid for single-fault programs', 'mar',
             'mean-average-rank')
def mar(ties: Ties, collapse: bool) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    elif (len(ties.faults) > 1):
        warning('Calling MAR on multi-fault program!')
        return nan
    num_locs = len(next(iter(ties.faults.values())))
    exp_vals = []
    # Handle perfect case
    ties.set_bug_understanding(BUModel.PERFECT)
    exp_vals.append(effort_exp_val(ties, 1, weffort=False, collapse=collapse))
    # Handle defective cases
    for i in range(2, num_locs):
        def strat(locs: int): return min(i, locs)
        ties.set_bug_understanding(BUModel(BUModel.IMPERFECT, strat))
        exp_vals.append(effort_exp_val(ties, 1, weffort=False,
                                       collapse=collapse))
    # Handle inept case
    if (num_locs > 2):
        ties.set_bug_understanding(BUModel.INEPT)
        exp_vals.append(effort_exp_val(ties, 1, weffort=False,
                                       collapse=collapse))
    return sum(exp_vals)/num_locs
