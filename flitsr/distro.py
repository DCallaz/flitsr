import sys
from matplotlib import pyplot as plt # type: ignore


def distro(file):
    lines = open(file).readlines()
    x = []
    y = []
    for line in lines:
        line = line.strip()
        if (line):
            vals = line.split()
            x.append(int(vals[0]))
            y.append(int(vals[1]))
    return x, y


if __name__ == "__main__":
    x, y = distro(sys.argv[1])
    plt.bar(x, y)
    plt.title("Fault distribution for project "+str(sys.argv[2]))
    plt.xlim([0, 32])
    plt.ylim([0, 1200])
    plt.show()
