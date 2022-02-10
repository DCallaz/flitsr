def one_top1(faults, sort, groups):
    i = 0
    score = sort[i][0]
    uuts = []
    # Get all UUTs with same score
    while (i < len(sort) and sort[i][0] == score):
        #print(i, sort[i][1])
        uuts.extend(groups[sort[i][1]])
        i += 1
    for fault in faults:
        if (fault in uuts):
            return True
    return False

def all_top1(faults, sort, groups):
    i = 0
    score = sort[i][0]
    uuts = []
    count = 0
    # Get all UUTs with same score
    while (i < len(sort) and sort[i][0] == score):
        #print(i, sort[i][1])
        uuts.extend(groups[sort[i][1]])
        i += 1
    for fault in faults:
        if (fault in uuts):
            count += 1
    return (count == len(faults))

def percent_top1(faults, sort, groups):
    i = 0
    score = sort[i][0]
    uuts = []
    count = 0
    # Get all UUTs with same score
    while (i < len(sort) and sort[i][0] == score):
        #print(i, sort[i][1])
        uuts.extend(groups[sort[i][1]])
        i += 1
    for fault in faults:
        if (fault in uuts):
            count += 1
    return (count/len(faults))*100
