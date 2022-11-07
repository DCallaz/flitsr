from suspicious import Suspicious

def remove_from(fault_groups, item):
    for s in fault_groups:
        if (item in fault_groups[s]):
            fault_groups[s].remove(item)

def linear(fault_groups):
    return [x for sub in fault_groups.values() for x in sub]

class cutoff_points:
    def getNames():
        all_names = dir(cutoff_points)
        names = [x for x in all_names if (not x.startswith("__")
            and x != "cut" and x != "getNames" and x != "method")]
        return names

    def cut(cutoff, fault_groups, scores, groups, formula, tp, tf, worst=False):
        func = getattr(cutoff_points, cutoff)
        return func(fault_groups, scores, groups, formula, tp, tf, worst)

    def oba(fault_groups, scores, groups, formula, tp, tf, worst):
        return cutoff_points.method(float('inf'), fault_groups, scores, groups, worst)

    def mba_dominator(fault_groups, scores, groups, formula, tp, tf, worst):
        sus = Suspicious(tf, tf, tp, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores, groups, worst)

    def mba_zombie(fault_groups, scores, groups, formula, tp, tf, worst):
        sus = Suspicious(0, tf, 0, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores, groups, worst)

    def mba_5_perc(fault_groups, scores, groups, formula, tp, tf, worst):
        size = 0
        for group in groups:
            size += len(group)
        return cutoff_points.method(int(size*0.05), fault_groups, scores,
                groups, worst, True)

    def mba_10_perc(fault_groups, scores, groups, formula, tp, tf, worst):
        size = 0
        for group in groups:
            size += len(group)
        return cutoff_points.method(int(size*0.1), fault_groups, scores,
                groups, worst, True)

    def mba_const_add(fault_groups, items, groups, formula, tp, tf, worst):
        tot_size = 0
        for group in groups:
            tot_size += len(group)
        sus = Suspicious(0, tf, 0, tp)
        zero = sus.execute(formula)
        new_scores = []
        stop_i = float('inf')
        i = 0
        f_num = 0
        size = 0
        while (i < len(items) and size+1 <= stop_i and (items[i][0] > zero or f_num == 0)):
            score = items[i][0]
            faults = 0
            while (i < len(items) and (items[i][0] == score)):
                if (items[i][1] in linear(fault_groups)):
                    remove_from(fault_groups, items[i][1])
                    faults += 1
                new_scores.append(items[i])
                size += len(groups[items[i][1]])
                i += 1
            if (faults != 0): # should've stopped already: size <= stop_i
                #recalculate stop amount
                f_num += faults
                stop_i = size + tot_size*0.01
        return new_scores

    def mba_optimal(fault_groups, items, groups, formula, tp, tf, worst):
        sus = Suspicious(0, tf, 0, tp)
        zero = sus.execute(formula)
        new_scores = []
        stop_i = float('inf')
        i = 0
        f_num = 0
        size = 0
        while (i < len(items) and size+1 <= stop_i and (items[i][0] > zero or f_num == 0)):
            score = items[i][0]
            faults = 0
            while (i < len(items) and (items[i][0] == score)):
                if (items[i][1] in linear(fault_groups)):
                    remove_from(fault_groups, items[i][1])
                    faults += 1
                new_scores.append(items[i])
                size += len(groups[items[i][1]])
                i += 1
            if (faults != 0): # should've stopped already: size <= stop_i
                #recalculate stop amount
                f_num += faults
                stop_i = size + size/(f_num+1)
        return new_scores

    def aba(fault_groups, items, groups, formula, tp, tf, worst):
        new_items = []
        i = 0
        temp_items = []
        while (i < len(items) and items[i][0] > 0.0):
            fault = False
            score = items[i][0]
            while (i < len(items) and items[i][0] == score):
                if (items[i][1] in linear(fault_groups)):
                    remove_from(fault_groups, items[i][1])
                    fault = True
                temp_items.append(items[i])
                i += 1
            if (fault):
                new_items.extend(temp_items)
                temp_items = []
        return new_items

    def method(stop_score, fault_groups, items, groups, worst, rank=False):
        new_items = []
        first_fault = -1
        i = 0
        size = 0
        while (i < len(items) and ((not rank and items[i][0] > stop_score)
            or (rank and size < stop_score) or first_fault == -1)):
            score = items[i][0]
            temp_items = []
            while (i < len(items) and items[i][0] == score):
                if (first_fault == -1 and items[i][1] in linear(fault_groups)):
                    remove_from(fault_groups, items[i][1])
                    first_fault = len(temp_items)
                temp_items.append(items[i])
                size += len(groups[items[i][1]])
                i += 1
            if (worst or score > stop_score or first_fault == -1):
                new_items.extend(temp_items)
            else:
                new_items.append(temp_items[first_fault])
        return new_items
