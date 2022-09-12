import subprocess
import re
import localize
import copy
import os

def parallel(d, table, test_map, counts, tiebrk):
    tables,count_arr = partition_table(d, table, test_map, counts)
    ranking = create_ranking(count_arr, tiebrk)
    return ranking

def partition_table(d, table, test_map, counts):
    output = subprocess.check_output(['java', '-jar',
        os.environ['FLITSR_HOME']+'/parallel-1.0-SNAPSHOT-jar-with-dependencies.jar', d]).decode('utf-8')
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
        tables.append(new_table)
        count_arr.append(new_counts)
    return tables,count_arr

def update_counts(counts, table):
    counts["tf"] = len(table)
    counts["f"] = [0]*len(table[0])
    for row in table:
        for i in range(len(row)):
            if (row[i]):
                counts["f"][i] += 1

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
        sorts.append(localize.localize(counts, 't', tiebrk))
    return merge_rankings(sorts)
