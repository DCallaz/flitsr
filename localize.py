from suspicious import Suspicious
import random

def get_counts(table):
    """
    Returns an array of the counts for each location in the following format:
        Location 1     ...
    [[ep, ef, np, nf], ...]
    """
    counts = [[0 for i in range(4)] for j in range(len(table[0])-2)]
    for i in range(0, len(table)):
        if (table[i][0] == False):
            continue
        for j in range(2, len(table[i])):
            if (table[i][j]):#location was executed
                if (table[i][1]):#Test case passed
                    counts[j-2][0] += 1#ep++
                else:#Test case failed
                    counts[j-2][1] += 1#ef++
            else:#location not executed
                if (table[i][1]):#Test case passed
                    counts[j-2][2] += 1#np++
                else:#Test case failed
                    counts[j-2][3] += 1#nf++
    return counts

def apply_formula(counts, formula):
    scores = []
    for i in range(0, counts["locs"]):
        sus = Suspicious(counts["f"][i], counts["tf"], counts["p"][i], counts["tp"])
        scores.append(sus.execute(formula))
    return scores

def get_exec(counts):
    execs = []
    for i in range(counts["locs"]):
       execs.append(counts["p"][i]+counts["f"][i])
    return execs

orig = None

def sort(zipped, order, tiebrk):
    if (tiebrk == 1):#Sorted by execution counts
        sort = sorted(zipped, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 2):#random ordering
        random.shuffle(zipped)
        sort = sorted(zipped, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 3):#original ranking tie break
        if (orig != None):#sort by original ranking, then execution count
            sort = sorted(zipped, key=lambda x: orig[x[1]][2], reverse=order)
            #print("sort1:",sort)
            sort = sorted(sort, key=lambda x: orig[x[1]][0], reverse=order)
            #print("sort2:",sort)
        else:#if no orig, still sort by current execution count
            sort = sorted(zipped, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
        #print("sort3:",sort)
    else:
        sort = sorted(zipped, key=lambda x: x[0], reverse=order)
    return sort

#Assumes the table is not empty
def localize(counts, formula, tiebrk, order=True):
    #counts = get_counts(table)
    scores = apply_formula(counts, formula)
    execs = get_exec(counts)
    zipped = list(map(list, zip(scores, range(counts["locs"]), execs)))
    return sort(zipped, order, tiebrk)
