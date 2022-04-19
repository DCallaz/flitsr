def first(faults, sort, groups, c):
    if (len(faults) == 0):
        return 0
    return method(faults, sort, groups, 1, collapse=c)

def average(faults, sort, groups, c):
    if (len(faults) == 0):
        return 0
    return method(faults, sort, groups, len(faults), True, c)

def median(faults, sort, groups, c):
    if (len(faults) == 0):
        return 0
    if (len(faults)%2 == 1):
        return method(faults, sort, groups, int((len(faults)+1)/2), False, c)
    else:
        m1 = method(faults, sort, groups, int(len(faults)/2), False, c)
        m2 = method(faults, sort, groups, int(len(faults)/2)+1, False, c)
        return (m1+m2)/2


def last(faults, sort, groups, c):
    if (len(faults) == 0):
        return 0
    return method(faults, sort, groups, len(faults), collapse=c)

#<---------------- Helper functions --------------->
def method(faults, sort, groups, target, avg=False, collapse=False):
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
        group_len = 0
        curr_faults = 0
        curr_faulty_groups = 0
        # Get all UUTs with same score
        while (i < len(sort) and sort[i][0] == score):
            #print(i, sort[i][1])
            uuts.extend(groups[sort[i][1]])
            group_len += 1
            # Check if fault is in group
            faulty_group = False
            for fault in faults:
                if (fault in groups[sort[i][1]]):
                    #print("found fault", fault)
                    actual += 1
                    curr_faults += 1
                    if (not faulty_group):
                        curr_faulty_groups += 1
                        faulty_group = True
                    #faults.remove(fault)
                    found = (actual >= target)
            i += 1
        if (avg):
            for j in range(0, curr_faults):
                if (collapse):
                    efforts.append(effort+(group_len-curr_faulty_groups)/(2))
                else:
                    efforts.append(effort+(len(uuts)+1)/(curr_faults+1)-1)
        if (not found):
            if (collapse):
                effort += group_len-curr_faulty_groups
            else:
                effort += len(uuts)-curr_faults
        else:
            if (collapse):
                effort += (group_len)/(curr_faulty_groups+1)
            else:
                effort += (len(uuts)+1)/(curr_faults+1)-1
    if (avg):
        return sum(efforts)/target
    else:
        return effort
