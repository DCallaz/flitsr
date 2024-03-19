from flitsr.tcm_input import read_table
from multiprocessing import Process, Event, Queue
import sys
import random
import math

def cond1(subset, table):
    np = 0
    nf = 0
    nnp = 0
    nnf = 0
    for i in range(len(table)):
        row = table[i]
        if (row[1]):
            np += 1
        else:
            nf += 1
        if (i in subset):
            if (row[1]):
                nnp += 1
            else:
                nnf += 1
    return abs((np - nnp) - (nf - nnf)) < 10

def cond2(subset, table, details):
    for i in range(len(details)):
        if (details[i][1]):
            mater = False
            for j in range(len(table)):
                row = table[j]
                if (j in subset and row[i+2]):
                    mater = True
                    break
            if (not mater):
                return False
    return True

def partition(table):
    passing = []
    failing = []
    for i in range(len(table)):
        if (table[i][1]):
            passing.append(i)
        else:
            failing.append(i)
    return passing, failing

def get_faulty(details):
    faulty = []
    for i in range(len(details)):
        if details[i][1]:
            faulty.append(i)
    return faulty

def delete_tests(file_name, subset):
    file = open(file_name)
    while (True):
        line = file.readline()
        if (line == ''):
            break
        if (line.startswith("#tests")):
            print(line, end='')
            line = file.readline()
            i = 0
            while (not line == '\n'):
                if (i in subset):
                    print(line, end='')
                i += 1
                line = file.readline()
        elif (line.startswith("#matrix")):
            print(line, end='')
            line = file.readline()
            i = 0
            while (not (line == '\n' or line == '')):
                if (i in subset):
                    print(line, end='')
                i += 1
                line = file.readline()
        print(line, end='')
    file.close()

def reduce_formal(event, q, table, details, tests, num_tests):
    passing, failing = partition(table)
    #print("passing", passing)
    #print("failing", failing)
    faulty = get_faulty(details)
    #print("faults", faulty)
    fail_tests = math.ceil((len(failing)/num_tests)*tests)
    #print("number of tests needed:", fail_tests)
    # set up map between faults and failing tests
    test_map = {}
    for fault in faulty:
        test_map[fault] = []
    for fail in failing:
        for fault in faulty:
            if (table[fail][fault+2]):
                test_map[fault].append(fail)
    #print("Test map", test_map)
    subset = failing.copy()
    # shuffle the list so that results vary on different executions
    random.shuffle(failing)
    #print("shuffled", failing)
    # run the reduction
    res = False
    for i in range(0, len(failing)):
        res = reduce_recursive(event, i, failing, subset, test_map, fail_tests)
        if (res or event.is_set()):
            break
    if (not res):
        # no solution possible, so return
        q.put(None)
        return
    subset.extend(random.sample(passing, tests - fail_tests))
    #print("extended", subset)
    q.put(subset)
    event.set()
    #print("formal finished")

def reduce_recursive(event, i, failing, subset, test_map, fail_tests):
    if (event.is_set()):
        return False
    #print("attempting to remove", failing[i], "("+str(i)+")")
    # try to add i to subset testing test_map
    violation = False
    # check for non-materializing fault
    for key in test_map:
        # if the test pool is a set of just this test, removing it will make the
        # test pool empty
        if (test_map[key] == [failing[i]]):
            #print("violation at", key, test_map[key])
            violation = True
            break
    if (violation):
        return False
    #print("no violations, continuing")
    # if no violation, remove test case
    removed_from = []
    for key in test_map:
        if (failing[i] in test_map[key]):
            test_map[key].remove(failing[i])
            removed_from.append(key)
    subset.remove(failing[i])
    #print("subset", subset)
    #print("test map", test_map)
    # check if number of test cases is enough
    if (len(subset) == fail_tests):
        #print("valid subset found")
        return True
    # iteratively try to recurse to the next position
    for j in range(i+1, len(failing)):
        res = reduce_recursive(event, j, failing, subset, test_map, fail_tests)
        if (res):
            return res
    #print("could not find valid solution")
    # add back this test and return to higher level
    for key in removed_from:
        test_map[key].append(failing[i])
    subset.append(failing[i])
    return False

def reduce_random(event, q, table, details, tests, num_tests):
    passing, failing = partition(table)
    #print("passing:",passing)
    #print("failing:",failing)
    ratio = len(failing)/num_tests
    valid = False
    while (not valid and not event.is_set()):
        valid = True
        #Generate random subset
        subset = random.sample(failing, math.ceil(ratio*tests))
        #print(subset)
        #Uncomment the following for random subsets with no conditions
        #break
        #Check conditions
        cond = cond2(subset, table, details)
        valid = valid and cond
        #if (not cond):
            #print("Condition 2 violated")
    if (event.is_set()):
        return
    subset.extend(random.sample(passing, tests - int(ratio*tests)))
    q.put(subset)
    event.set()
    #print("random finished")

if __name__ == "__main__":
    if (len(sys.argv) < 3):
        print("USAGE: reduce <input file> [<no. of tests>/<% reduction>%]")
        quit()
    d = sys.argv[1]
    table,num_locs,num_tests,details = read_table(d)
    #Calculate number of tests to include
    tests = 0
    if (sys.argv[2].endswith('%')):
        tests = int(num_tests*(float(sys.argv[2][:-1])/100))
    else:
        tests = int(sys.argv[2])
    event = Event()
    q = Queue()
    p1 = Process(target=reduce_formal, args=(event, q, table, details, tests,
        num_tests, ))
    #subset = reduce_formal(table, details, tests, num_tests)
    p2 = Process(target=reduce_random, args=(event, q, table, details, tests,
        num_tests, ))
    #subset = reduce_random(table, details, tests, num_tests)
    p1.start()
    p2.start()
    subset = q.get()
    p1.join()
    p2.join()
    #print(subset)
    if (subset == None):
        quit()
    delete_tests(d, subset)
