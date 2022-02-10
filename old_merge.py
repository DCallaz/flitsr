import sys

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("USAGE: python3 merge.py <localize file> <feedback file>")
        exit()
    loc = open(sys.argv[1])
    feed = open(sys.argv[2])
    improve = 0
    improve_rate = 0
    worse = 0
    worse_rate = 0
    total = 0
    aawe_loc = 0
    aawe_feed = 0
    for i in range(2280):
        lf = feed.readline()
        ll = loc.readline()
        if (lf.startswith("wasted effort") and ll.startswith("wasted effort")):
            total += 1
            scoref = float(lf.split(": ")[1])
            scorel = float(ll.split(": ")[1])
            aawe_loc += scorel
            aawe_feed += scoref
            print(scorel, scoref, scoref - scorel)
            if (scoref > scorel):
                worse += 1
                worse_rate += scoref - scorel
            elif (scoref < scorel):
                improve += 1
                improve_rate += scorel - scoref
        elif (lf == ll):
            print(lf, end="")
    aawe_loc = aawe_loc/total
    aawe_feed = aawe_feed/total
    print(str(worse*100/total)+"% worse result", worse_rate/worse, "rate")
    print(str(improve*100/total)+"% improved result", improve_rate/improve,"rate")
    print(str((total-worse-improve)*100/total)+"% identical result")
    print((aawe_loc-aawe_feed)*100/aawe_loc, "% improvement")
