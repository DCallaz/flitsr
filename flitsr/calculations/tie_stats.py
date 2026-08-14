from flitsr.calculations.calc_decorator import calculation
from flitsr.tie import Ties


@calculation('tie size', 'Display the average size of ties in the ranking',
             'tie-size')
def tie_size(ties: Ties, collapse: bool):
    size_sum = 0
    for tie in ties:
        size_sum += tie.len(collapse)
    return size_sum/len(ties)


@calculation('critical tie size', 'Display the average size of only the '
             'critical ties in the ranking', 'crit-tie-size')
def critical_tie_size(ties: Ties, collapse: bool):
    size_sum = 0
    num_crit_ties = 0
    for tie in ties:
        if (tie.num_faults() > 0):
            size_sum += tie.len(collapse)
            num_crit_ties += 1
    if (num_crit_ties == 0):
        return 0.0
    return size_sum/num_crit_ties


@calculation('number of critical ties', 'Display the number of critical ties '
             'in the ranking', 'crit-tie-num')
def num_critical_ties(ties: Ties, collapse: bool):
    num_crit_ties = 0
    for tie in ties:
        if (tie.num_faults() > 0):
            num_crit_ties += 1
    return num_crit_ties


@calculation('faults per critical tie', 'Display the average number of faults '
             'in each of the critical ties in the ranking', 'crit-tie-faults')
def num_critical_faults(ties: Ties, collapse: bool):
    num_faults = 0
    num_crit_ties = 0
    for tie in ties:
        if (tie.num_faults() > 0):
            num_faults += tie.num_faults()
            num_crit_ties += 1
    if (num_crit_ties == 0):
        return 0.0
    return num_faults/num_crit_ties


@calculation('fault locs per critical tie', 'Display the average number of '
             'fault locations in each of the critical ties in the ranking',
             'crit-tie-fault-locs')
def num_critical_fault_locs(ties: Ties, collapse: bool):
    num_fault_locs = 0
    num_crit_ties = 0
    for tie in ties:
        if (tie.num_faults() > 0):
            num_fault_locs += tie.num_active_fault_locs(collapse)
            num_crit_ties += 1
    if (num_crit_ties == 0):
        return 0.0
    return num_fault_locs/num_crit_ties
