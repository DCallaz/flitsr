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
    for loc in counts:
        sus = Suspicious(loc[1], loc[3]+loc[1], loc[0], loc[2]+loc[0])
        if (formula == 't'):
            scores.append(sus.tarantula())
        elif (formula == 'o'):
            scores.append(sus.ochai())
        elif (formula == 'j'):
            scores.append(sus.jaccard())
        elif (formula == 'd'):
            scores.append(sus.dstar())
        elif (formula == 'g'):
            scores.append(sus.gp13())
        elif (formula == 'n'):
            scores.append(sus.naish2())
        elif (formula == 'w'):
            scores.append(sus.wong2())
        elif (formula == 'v'):
            scores.append(sus.overlap())
        elif (formula == 'h'):
            scores.append(sus.harmonic())
    return scores

def get_exec(counts):
    execs = []
    for loc in counts:
       execs.append(loc[0]+loc[1])
    return execs


orig = None

def sort(zipped, table, order, tiebrk):
    if (tiebrk == 1):#Sorted by execution counts
        sort = sorted(zipped, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 2):#random ordering
        random.shuffle(zipped)
        sort = sorted(zipped, key=lambda x: x[0], reverse=order)
    elif (tiebrk == 3):#original ranking tie break
        if (orig != None):#sort by original ranking, then execution count
            sort = sorted(zipped, key=lambda x: orig[x[1]][2], reverse=order)
            sort = sorted(sort, key=lambda x: orig[x[1]][0], reverse=order)
        else:#if no orig, still sort by current execution count
            sort = sorted(zipped, key=lambda x: x[2], reverse=order)
        sort = sorted(sort, key=lambda x: x[0], reverse=order)
    else:
        sort = sorted(zipped, key=lambda x: x[0], reverse=order)
    return sort

#Assumes the table is not empty
def localize(table, formula, tiebrk, order=True):
    counts = get_counts(table)
    scores = apply_formula(counts, formula)
    execs = get_exec(counts)
    zipped = list(map(list, zip(scores, range(len(table[0])-2), execs)))
    return sort(zipped, table, order, tiebrk)
