import sys

if __name__ == "__main__":
    weff=["first", "avg", "med"]
    iters = int(sys.argv[1])
    for metric in ["tar", "och", "jac", "dst"]:
        max_file = open("feed_rndm_max_"+metric+"_weff", "w")
        avg_file = open("feed_rndm_avg_"+metric+"_weff", "w")
        min_file = open("feed_rndm_min_"+metric+"_weff", "w")
        f = open("feed_rndm_"+metric+"_weff", "r")
        broken = False
        while (not broken):
            first = []
            avg = []
            med = []
            variant = None
            for i in range(0, iters):
                l = f.readline()
                if (l == ''):
                    broken = True
                    break
                if (not variant):
                    variant = l.split("_")[0] +"_" + l.split("_")[1] + ".txt"
                first.append(float(f.readline().split(": ")[1].strip()))
                avg.append(float(f.readline().split(": ")[1].strip()))
                med.append(float(f.readline().split(": ")[1].strip()))
                f.readline()
            if (broken):
                break
            print(variant, file=max_file)
            print("wasted effort (first):", max(first), file=max_file)
            print("wasted effort (avg):", max(avg), file=max_file)
            print("wasted effort (median):", max(med), file=max_file)
            print("--------------------------", file=max_file)

            print(variant, file=min_file)
            print("wasted effort (first):", min(first), file=min_file)
            print("wasted effort (avg):", min(avg), file=min_file)
            print("wasted effort (median):", min(med), file=min_file)
            print("--------------------------", file=min_file)

            print(variant, file=avg_file)
            print("wasted effort (first):", sum(first)/len(first), file=avg_file)
            print("wasted effort (avg):", sum(avg)/len(avg), file=avg_file)
            print("wasted effort (median):", sum(med)/len(med), file=avg_file)
            print("--------------------------", file=avg_file)
        f.close()
        max_file.close()
        min_file.close()
        avg_file.close()
