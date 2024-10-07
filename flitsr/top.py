from flitsr.tie import Ties, Tie


def one_top1(ties: Ties) -> bool:
    tie = get_top1(ties)
    for fault in ties.faults.values():
        for loc in fault:
            if (loc in tie.elems()):
                return True
    return False


def all_top1(ties: Ties) -> bool:
    tie = get_top1(ties)
    count = 0
    for fault in ties.faults.values():
        for loc in fault:
            if (loc in tie.elems()):
                count += 1
                break  # Only consider first location of fault
    return (count == len(ties.faults))


def percent_top1(ties: Ties) -> float:
    if (len(ties.faults) == 0):
        return 100
    else:
        tie = get_top1(ties)
        count = 0
        for fault in ties.faults.values():
            for loc in fault:
                if (loc in tie.elems()):
                    count += 1
                    break
        return (count/len(ties.faults))*100


def size_top1(ties: Ties) -> int:
    tie = get_top1(ties)
    return len(tie.elems())


# <------------------------- Helper functions ---------------------->


def get_top1(ties: Ties) -> Tie:
    tie_iter = iter(ties)
    return next(tie_iter)
