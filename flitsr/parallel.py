import subprocess
import re
from flitsr.suspicious import Suspicious
import copy
import os

def parallel(d, table, test_map, counts, tiebrk, metric, parType):
    tables,count_arr = partition_table(d, table, test_map, counts, parType)
    #rankings = get_rankings(count_arr, tiebrk, metric)
    return tables,count_arr

def partition_table(d, table, test_map, counts, parType):
    output = subprocess.check_output(['java', '-jar',
        os.environ['FLITSR_HOME']+'/src/parallel-1.0-SNAPSHOT-jar-with-dependencies.jar',
        d, parType]).decode('utf-8')
    partitions = re.split("partition \d+\n", output)[1:]
    tables = []
    count_arr = []
    for partition in partitions:
        new_table = []
        new_counts = copy.deepcopy(counts)
        tests = [ int(i) for i in partition.strip().split("\n")]
        for test in tests:
            new_table.append(table[test_map[test]])
        update_counts(new_counts, new_table)
        trim_elements(new_counts, new_table)
        tables.append(new_table)
        count_arr.append(new_counts)
    return tables,count_arr

def update_counts(counts, table):
    """Update failing test counts"""
    counts["tf"] = len(table)
    counts["f"] = [0]*(counts['locs'])
    for row in table:
        for i in range(1, len(row)):
            if (row[i]):
                counts["f"][i-1] += 1

def trim_elements(counts, table):
    """Remove elements that are not in this block (i.e. ef = 0)"""
    toKeep = []
    p = counts['p']
    f = counts['f']
    locs = counts['locs']
    counts['f'] = []
    counts['p'] = []
    counts['map'] = []
    counts['locs'] = 0
    for i in range(locs):
        if (f[i] > 0):
            counts['f'].append(f[i])
            counts['p'].append(p[i])
            counts['map'].append(i)
            counts['locs'] += 1
            toKeep.append(i)
    for i in range(len(table)):
        new_row = [table[i][0]]
        for elem in toKeep:
            new_row.append(table[i][elem+1])
        table[i] = new_row

def get_rankings(count_arr, tiebrk, metric):
    sorts = []
    for counts in count_arr:
        # Get ranking of remaining elements
        ranking = Suspicious.apply_formula(new_counts, metric, tiebrk)
        # map back the remaining elements to their original indexes
        for rank in ranking:
            rank[1] = new_counts['map'][rank[1]]
        sorts.append(ranking)
    return sorts

def merge_rankings(rankings):
    single = []
    for rank in rankings:
        val = 2**64
        i = 0
        score = rank[i][0]
        for i in range(len(rank)):
            if (rank[i][0] != score):
                score = rank[i][0]
                val -= 1
            single.append((val, rank[i][1], rank[i][2]))
    return single

def create_ranking(count_arr, tiebrk):
    sorts = []
    for i in range(len(count_arr)):
        counts = count_arr[i]
        sorts.append(Suspicious.apply_formula(counts, 'ochiai', tiebrk))
    return merge_rankings(sorts)
