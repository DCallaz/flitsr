import numpy as np
from flitsr.suspicious import Suspicious

def explorer(activityMatrix, errorVector, numcomp, sbflMetric, numUniverse, maxUniverse, pBernoulli = 0):

    rankingList = []
    universe = []
    maxRefinement = maxUniverse
    numRef = 0
    if np.isclose(errorVector.sum(), 0):
        return rankingList
    else:
        universe.insert(0, errorVector.copy())  #insert as enqueue
        toContinue = len(universe) > 0
        while toContinue:
            e = np.array(universe.pop())    #remove as dequeue
            ranking = np.zeros((activityMatrix.shape[1], 3))
            for i in range(activityMatrix.shape[1]):
                ranking[i, 0] = i
                # get counts
                c = activityMatrix[:, i]
                tf = (e > 0).sum()
                tp = (e == 0).sum()
                ef = (e[(c > 0)] > 0).sum()
                ep = (e[(c > 0)] == 0).sum()
                ranking[i, 1] = Suspicious(ef, tf, ep, tp).execute(sbflMetric)
            u, idx = np.unique(-ranking[:, 1], return_inverse=True)
            ranking[:, 2] = idx
            ranking = ranking[(ranking[:, -1]).argsort()]
            rankingList.append(ranking)
            for i in range(min(numUniverse, numcomp)):
                if ranking[i, 1] > 0:
                    toSuppress = int(ranking[i, 0])
                    e_refined = e.copy()
                    testsToRerun = (activityMatrix[:, toSuppress] == 1)
                    for j in range(len(testsToRerun)):
                        if testsToRerun[j]:
                            e_refined[j] = np.random.binomial(1, pBernoulli, size = 1)[0]
                    if not (any([(e_refined == a_s).all() for a_s in universe])) and not (np.sum(e_refined) == 0) and numRef <= maxRefinement:
                        universe.insert(0, e_refined)
                        numRef += 1
            toContinue = len(universe) > 0 and numUniverse > 0
    return rankingList

def merge(rankingList, numcomp):

    bestScoreList = np.zeros(numcomp)
    sortedRankingList = np.zeros((numcomp, 3))

    for i in range(len(rankingList)):
        currlist = rankingList[i]
        for item in currlist:
            comp = int(item[0])
            compScore = item[1]
            if compScore > bestScoreList[comp]:
                bestScoreList[comp] = compScore


    for i in range(numcomp):
        sortedRankingList[i, 0] = i
        sortedRankingList[i, 1] = bestScoreList[i]
    u, idx = np.unique(-sortedRankingList[:, 1], return_inverse=True)
    sortedRankingList[:, 2] = idx
    sortedRankingList = sortedRankingList[(sortedRankingList[:, -1]).argsort()]

    return sortedRankingList
