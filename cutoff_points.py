from suspicious import Suspicious

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
        return cutoff_points.method(float('inf'), fault_groups, scores, worst)

    def mba_dominator(fault_groups, scores, groups, formula, tp, tf, worst):
        sus = Suspicious(tf, tf, tp, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores, worst)

    def mba_zombie(fault_groups, scores, groups, formula, tp, tf, worst):
        sus = Suspicious(0, tf, 0, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores, worst)

    def mba_optimal(fault_groups, items, groups, formula, tp, tf, worst):
        new_scores = []
        stop_i = float('inf')
        i = 0
        f_num = 0
        size = 0
        while (i < len(items) and size+1 <= stop_i):
            score = items[i][0]
            faults = 0
            while (i < len(items) and (items[i][0] == score)):
                if (items[i][1] in fault_groups):
                    faults += 1
                new_scores.append(items[i])
                size += len(groups[items[i][1]])
                i += 1
            if (faults != 0):
                #recalculate stop amount
                f_num += faults
                stop_i = size + size/f_num
        return new_scores

    def aba(fault_groups, items, groups, formula, tp, tf, worst):
        new_items = []
        i = 0
        temp_items = []
        while (i < len(items) and items[i][0] > 0.0):
            fault = False
            score = items[i][0]
            while (i < len(items) and items[i][0] == score):
                if (items[i][1] in fault_groups):
                    fault = True
                temp_items.append(items[i])
                i += 1
            if (fault):
                new_items.extend(temp_items)
                temp_items = []
        return new_items


    def method(stop_score, fault_groups, items, worst):
        new_items = []
        first_fault = -1
        i = 0
        while (i < len(items) and (items[i][0] > stop_score or first_fault == -1)):
            score = items[i][0]
            temp_items = []
            while (i < len(items) and items[i][0] == score):
                if (items[i][1] in fault_groups and first_fault == -1):
                    first_fault = len(temp_items)
                temp_items.append(items[i])
                i += 1
            if (worst or score > stop_score or first_fault == -1):
                new_items.extend(temp_items)
            else:
                new_items.append(temp_items[first_fault])
        return new_items

        #for item in scores:
            #if (item[1] in fault_groups):
                #first_score = item[0]
                #found_one = True
            #if ((item[0] > stop_score) or (not found_one) or (item[0] == first_score)):
                #new_scores.append(item)
            #else:
                #break
        #return new_scores