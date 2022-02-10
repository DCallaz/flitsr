def first(faults, sort, groups):
    return method(faults, sort, groups, 1)

def average(faults, sort, groups):
    return method(faults, sort, groups, len(faults), True)

def last(faults, sort, groups):
    return method(faults, sort, groups, len(faults))

#<---------------- Helper functions --------------->
def method(faults, sort, groups, target, avg=False):
    #print("faults:", faults)
    found = False
    actual = 0
    effort = 0
    efforts = []
    i = 0
    #print("Groups:",groups)
    #print("Length:",len(groups))
    #print("Sort:",sort)
    while (not found):
        score = sort[i][0]
        uuts = []
        # Get all UUTs with same score
        while (i < len(sort) and sort[i][0] == score):
            #print(i, sort[i][1])
            uuts.extend(groups[sort[i][1]])
            i += 1
        #print(uuts)
        # Check if fault is in group
        curr_faults = 0
        for fault in faults:
            if (fault in uuts):
                #print("found fault", fault)
                actual += 1
                curr_faults += 1
                #faults.remove(fault)
                found = (actual >= target)
        if (avg):
            for j in range(0, curr_faults):
                efforts.append(effort+(len(uuts)-curr_faults+1)/(2))
        if (not found):
            effort += len(uuts)-curr_faults
        else:
            effort += (len(uuts)-curr_faults+1)/(curr_faults+1)
    if (avg):
        return sum(efforts)/target
    else:
        return effort
