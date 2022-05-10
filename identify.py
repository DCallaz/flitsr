import sys

if __name__ == "__main__":
    res = open("results").readlines()
    funcs = ["localize", "feedback"]
    vals = [0]*len(funcs)
    i = 0
    fs = 0
    while (res[i].strip() != sys.argv[1]):
        i += 1
    while (fs < len(funcs)):
        while (res[i].strip() not in funcs):
            i += 1
        fs += 1
        index = funcs.index(res[i].strip())
        i += 1
        while (sys.argv[2] not in res[i].strip()):
            i += 1
        vals[index] = float(res[i].strip().split(": ")[-1])
    if (vals[0] > vals[1]):
        print((vals[0]-vals[1])/vals[0] * 100)
    else:
        print(-(vals[1]-vals[0])/vals[1] * 100)
