from flitsr.tie import Ties
from flitsr.calculations.calc_decorator import calculation
from flitsr.calculations.exp_values import effort_exp_val


def nth_print_name(ties: Ties, collapse: bool, n: int):
    return f"exam score ({n})"


@calculation(nth_print_name, 'Display the EXAM/Expense score to the nth '
             'fault', 'exam', 'expense')
def exam_score(ties: Ties, collapse: bool, n: int) -> float:
    if (len(ties.faults) == 0):
        return 0.0
    exp_val = effort_exp_val(ties, n, weffort=False, collapse=collapse)
    return exp_val/ties.size(collapse)
