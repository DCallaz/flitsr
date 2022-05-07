from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (7, 5)
import sys

imprvs = sys.stdin.readlines()
n = 11
m = {
    "tar": "Tarantula",
    "och": "Ochiai",
    "dst": "DStar",
    "flitsr": "FLITSR",
    "multi": "FLITSR*",
    "med": "Median",
    "first": "First"
}
data = {
    "first": {
        "Tarantula": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        },
        "Ochiai": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        },
        "DStar": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        }
    },
    "med": {
        "Tarantula": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        },
        "Ochiai": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        },
        "DStar": {
            "FLITSR": [0]*n,
            "FLITSR*": [0]*n
        }
    }
}
colors = {
    'Tarantula':'b',
    'Ochiai':'g',
    'DStar': 'r'
}
styles = {
    'FLITSR':'-',
    'FLITSR*':'--'
}
for line in imprvs:
    line = line.strip()
    f = line.split(",")
    data[f[3]][m[f[2]]][m[f[1]]][int(f[0])-1] = float(f[4])
x = list(range(1, n+1))
for measure in data.keys():
    plt.axhline(y=0, color='k', label='_nolegend_')
    legend=[]
    metrics = data[measure]
    for metric in metrics.keys():
        methods = metrics[metric]
        for method in methods.keys():
            plt.plot(x, methods[method], colors[metric]+styles[method])
            legend.append(method+" "+metric)
    #plt.title(m[measure]+" fault")
    plt.legend(legend, fontsize=9.5, loc='lower right')
    plt.ylim([-1, 1])
    plt.grid()
    plt.show()
