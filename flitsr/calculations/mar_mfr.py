from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation
from flitsr.calculations.exp_values import effort_exp_val
from flitsr.calculations.bu_model import BUModel


def mfr_print_name(ties: Ties, collapse: bool, n: int):
    return f"mean first rank ({n})"


@calculation(mfr_print_name, 'Display the mean first rank (MFR) to the nth '
             'fault', 'mfr', 'mean-first-rank')
def mfr(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    ties.set_bug_understanding(BUModel.PERFECT)
    return effort_exp_val(ties, n, weffort=False, collapse=collapse)


def mar_print_name(ties: Ties, collapse: bool, n: int):
    return f"mean average rank ({n})"


@calculation(mar_print_name, 'Display the mean average rank (MAR) to the nth '
             'fault', 'mar', 'mean-average-rank')
def mar(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    max_fault_locs = max(len(locs) for locs in ties.faults.values())
    exp_vals = []
    # Handle perfect case
    ties.set_bug_understanding(BUModel.PERFECT)
    exp_vals.append(effort_exp_val(ties, n, weffort=False, collapse=collapse))
    # Handle defective cases
    for i in range(2, max_fault_locs):
        def strat(locs: int): return min(i, locs)
        ties.set_bug_understanding(BUModel(BUModel.DEFECTIVE, strat))
        exp_vals.append(effort_exp_val(ties, n, weffort=False,
                                       collapse=collapse))
    # Handle inept case
    if (max_fault_locs > 1):
        ties.set_bug_understanding(BUModel.INEPT)
        exp_vals.append(effort_exp_val(ties, n, weffort=False,
                                       collapse=collapse))
    return sum(exp_vals)/max_fault_locs
