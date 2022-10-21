from suspicious import Suspicious

class cutoff_points:
    def getNames():
        all_names = dir(cutoff_points)
        names = [x for x in all_names if (not x.startswith("__")
            and x != "cut" and x != "getNames" and x != "method")]
        return names

    def cut(cutoff, fault_groups, scores, formula, tp, tf):
        func = getattr(cutoff_points, cutoff)
        return func(fault_groups, scores, formula, tp, tf)

    def oba(fault_groups, scores, formula, tp, tf):
        return cutoff_points.method(float('inf'), fault_groups, scores)

    def mba_dominator(fault_groups, scores, formula, tp, tf):
        sus = Suspicious(tf, tf, tp, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores)

    def mba_zombie(fault_groups, scores, formula, tp, tf):
        sus = Suspicious(0, tf, 0, tp)
        score = sus.execute(formula)
        return cutoff_points.method(score, fault_groups, scores)

    def mba_optimal(fault_groups, scores, formula, tp, tf):
        new_scores = []
        stop_i = float('inf')
        i = 0
        f_num = 0
        for item in scores:
            i += 1
            new_scores.append(item)
            if (item[1] in fault_groups):
                #recalculate stop amount
                f_num += 1
                stop_i = i + (i - f_num)/f_num
            if (i > stop_i):
                break
        return new_scores

    def method(stop_score, fault_groups, scores):
        new_scores = []
        found_one = False
        first_score = -1
        for item in scores:
            if (item[1] in fault_groups):
                first_score = item[0]
                found_one = True
            if ((item[0] > stop_score) or (not found_one) or (item[0] == first_score)):
                new_scores.append(item)
            else:
                break
        return new_scores
