import sys

if __name__ == "__main__":
    metrics = [("tar_", "Tarantula"), ("och_", "Ochiai"), ("dst_", "DStar")]
    modes = [("", "Base metric"), ("flitsr_", "FLITSR"), #("feed_tie_", "feedback tie"),
            #("feed_multi_", "feedback multi"),
            ("flitsr_multi_", "FLITSR*")]
            #("feed_rndm_max_", "feedback random max"), ("feed_rndm_avg_",
            #"feedback random average"), ("feed_rndm_min_", "feedback random min")]
    calcs = ["first",
            #"avg", "last",
            "top1", "sizet1",
            "med"]
    files = []
    total = 0
    avgs = []
    rel = False
    if (len(sys.argv) > 1 and sys.argv[1] == "rel"):
        size = int(open("../size").readline())
        rel = True

    for metric in metrics:
        for mode in modes:
            files.append(open(mode[0]+metric[0]+"weff"))
            for calc in calcs:
                avgs.append(0)

    while (True):
        lines = []
        for f in files:
            f.readline()
            for calc in calcs:
                lines.append(f.readline())
            f.readline()
        if (lines[0] == ''):
            break
        total += 1
        for i in range(0, len(lines)):
            if (rel):
                avgs[i] += float(lines[i].split(": ")[1])*100/size
            else:
                avgs[i] += float(lines[i].split(": ")[1])

    i = 0
    for metric in metrics:
        print(metric[1])
        for mode in modes:
            print('\t', mode[1])
            for calc in calcs:
                avgs[i] = avgs[i]/total
                if (rel):
                    print("\t\t",calc+":", str(avgs[i])+"%")
                else:
                    print("\t\t",calc+":", avgs[i])
                i += 1
