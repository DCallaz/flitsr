import sys
from matplotlib import pyplot as plt

lines = sys.stdin.readlines()
x = []
y = []
for line in lines:
    line = line.strip()
    if (line):
        vals = line.split()
        x.append(int(vals[1]))
        y.append(int(vals[0]))
plt.bar(x, y)
plt.title("Fault distribution for project "+str(sys.argv[1]))
plt.xlim([0, 32])
plt.ylim([0, 1200])
plt.show()
