from flitsr.calculations.calc_decorator import calculation
from flitsr.tie import Ties


@calculation('fault number', 'Display the number of faults in the program',
             'fault-num')
def num_faults(ties: Ties, collapse: bool):
    return len(ties.faults)


@calculation('fault ids', 'Display the IDs of the faults in the program',
             'fault-ids')
def fault_ids(ties: Ties, collapse: bool):
    return list(ties.faults.keys())


@calculation('fault elements', 'Display the elements that are faulty in the '
             'program', 'fault-elems')
def fault_elems(ties: Ties, collapse: bool):
    return [e for es in ties.faults.values() for e in es]


@calculation('fault info', 'Display all info of the faults in the program',
             'fault-all')
def fault_info(ties: Ties, collapse: bool):
    return ties.faults
