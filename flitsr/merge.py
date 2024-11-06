import re
from flitsr.percent_at_n import combine
import os
from os import path as osp
from io import TextIOWrapper
from scipy.stats import wilcoxon
from argparse import ArgumentParser, Action, FileType
import argcomplete
from flitsr.file import File
from flitsr.suspicious import Suspicious
from typing import Set, Dict, List, Tuple, Collection

PERC_N = "percentage at n"


class Avg:
    """Holds a partially constructed average"""
    def __init__(self, size=None, percn=False):
        self.all = []
        self.adds = 0
        self.percn = percn
        self.rel = False
        if (size is not None):
            self.rel = True
            self.size = size

    def add(self, val):
        self.all.append(val)
        self.adds += 1

    def eval(self):
        if (self.percn):
            return self.all
        elif (self.rel):
            return sum(s*100/self.size for s in self.all)/self.adds
        else:
            return sum(self.all)/self.adds

    def significance(self, avg: 'Avg'):
        diff = 1.0 if (self.all == avg.all) else \
            wilcoxon(self.all, avg.all, "pratt", method="approx").pvalue
        if (diff >= 0.05):
            return ('equal', diff)
        else:
            greater = wilcoxon(self.all, avg.all, "pratt", method="approx",
                               alternative="greater").pvalue
            less = wilcoxon(self.all, avg.all, "pratt", method="approx",
                            alternative="less").pvalue
        if (greater < 0.05):
            return ('greater', greater)
        else:
            return ('less', less)


def readBlock(file: File) -> List[str]:
    block = []
    line = file.readline()
    if (": " not in line):
        line = file.readline()
    while (line != "" and not re.match("^-+$", line)):
        block.append(line)
        line = file.readline()
    return block


def find_dirs(dirs: List[str], path, depth=1, max=None, incl=[], excl=[]):
    for dir in os.scandir(path):
        if (dir.is_dir()):
            new_path = dir.path
            if ((max and depth >= max) or
                (not max and any(f.endswith('.results') for f in
                                 os.listdir(new_path)))):
                if (dir.name not in excl and (len(incl) == 0 or
                                              dir.name in incl)):
                    dirs.append(new_path+"/")
            else:
                find_dirs(dirs, new_path, depth=depth+1, max=max, incl=incl,
                          excl=excl)


def ci_eq(str1: str, str2: str):
    """ Case insensitive equality check for strings """
    return str1.casefold() == str2.casefold()


def ci_in(str1: str, col: Collection[str]):
    """ Case insensitive check for strings in a list """
    return str1.casefold() in map(str.casefold, col)


def merge(recurse: bool, max: int, incl: List[str], excl: List[str], rel: bool,
          output_file: TextIOWrapper, perc_file: TextIOWrapper,
          tex_file: TextIOWrapper, dec=2, group='metric', incl_calcs=None,
          percs=None, incl_metrics=None, flitsrs=None, sign=None,
          sign_less=[]):
    metrics: Set[str] = set()
    modes: Set[str] = set()
    calcs: Set[str] = set()
    #           dir       mode      metric
    files: Dict[str, Dict[str, Dict[str, File]]] = {}
    #          mode      metric    calc
    avgs: Dict[str, Dict[str, Dict[str, Avg]]] = {}
    if (rel):
        if (not recurse):
            size = int(open("../size").readline())
    dirs = [""]
    if (recurse):
        dirs = []
        find_dirs(dirs, ".", max=max, incl=incl, excl=excl)

    if (rel):
        sizes = {}
    results_check = re.compile("^(?:([\\w_]*)_)?(\\w+)\\.results$")
    for d in dirs:
        files.setdefault(d, {})
        for file in os.scandir(osp.normpath(d)):
            m = results_check.match(file.name)
            if (m):
                mode = m.group(1) or ""
                modes.add(mode)
                metric = m.group(2)
                metrics.add(metric)
                files[d].setdefault(mode, {})[metric] = File(file)
                avgs.setdefault(mode, {}).setdefault(metric, {})
        if (rel):
            sizes[d] = int(open(osp.join(d, "../size")).readline())

    # Collect all the results
    for d in dirs:
        for mode in modes:
            for metric in metrics:
                try:
                    block = readBlock(files[d][mode][metric])
                except Exception:
                    continue
                while (block != []):
                    for line in block:
                        line_s = line.split(": ")
                        calc = line_s[0]
                        calcs.add(calc)
                        if (calc == PERC_N):
                            vals = line_s[1].split(",")
                            avgs[mode][metric].setdefault(calc, Avg(percn=True)).add(
                                (float(vals[0]), [float(x) for x in vals[1:]]))
                        else:
                            s = None
                            if (rel):
                                s = sizes[d] if recurse else size
                            avgs[mode][metric].setdefault(calc, Avg(s)).add(
                                    float(line_s[1]))
                    block = readBlock(files[d][mode][metric])

    def print_heading(name, tabs):
        name_disp = name.replace("_", " ").title()
        print('\t'*tabs, name_disp, sep='', file=output_file)
        if (ci_in(PERC_N, calcs) and perc_file != output_file):
            print('\t'*tabs, name_disp, sep='', file=perc_file)

    def print_tex_heading(mode, metric):
        metric_disp = metric.replace("_", " ").title()
        mode_disp = mode.replace("_", " ").title()
        print('%25s' % (metric_disp + " " + mode_disp), end=" & ",
              file=tex_file)

    def print_results(mode, metric):
        for j, calc in enumerate(sorted(calcs)):
            if (ci_eq(calc, PERC_N)):
                comb = combine(avgs[mode][metric][calc].eval())
                print("\t\t", calc+": ", comb, sep='', file=perc_file)
            else:
                avg = avgs[mode][metric][calc]
                if (not rel and percs is not None and ci_in(calc, percs)):
                    result = round(100*avg.eval(), dec)
                else:
                    result = round(avg.eval(), dec)
                sign_disp = ""
                if (sign is not None):
                    signis: Dict[str, List[Tuple[str, float]]] = {}
                    if (sign == 'type'):
                        for m_alt in modes:
                            if (m_alt == mode or not
                                (ci_in(m_alt, avgs) and
                                 ci_in(metric, avgs[m_alt]))):
                                continue
                            r, p = avg.significance(avgs[m_alt][metric][calc])
                            signis.setdefault(r, []).append((m_alt, p))
                    else:
                        for m_alt in metrics:
                            if (m_alt == metric or not
                                (ci_in(mode, avgs) and
                                 ci_in(m_alt, avgs[mode]))):
                                continue
                            r, p = avg.significance(avgs[mode][m_alt][calc])
                            signis.setdefault(r, []).append((m_alt, p))
                    sign_disp = f" (significantly {signis})"
                print("\t\t", calc+": ", result, sign_disp, sep='',
                      file=output_file)
                if (tex_file):
                    # process TeX significance only for advanced types
                    sign_disp = ''
                    if (sign == 'type' and not ci_eq(mode, 'base')):
                        try:
                            r, p = avg.significance(
                                    avgs['base'][metric][calc])
                            if ((calc in sign_less and r == 'less') or
                                (calc not in sign_less and r == 'greater')):
                                sign_disp = '\\tp'
                        except KeyError:
                            pass
                    end = (" & " if j+1 != len(calcs) else " \\\\\n")
                    print('{: <3}'.format(sign_disp),
                          '{: >10.{}f}'.format(result, min(dec, 8)),
                          end=end, file=tex_file)

    # Print out merged results
    if (ci_eq(group, 'metric')):
        zipped = [(mo, me) for me in sorted(metrics) for mo in sorted(modes)]
    else:
        zipped = [(mo, me) for mo in sorted(modes) for me in sorted(metrics)]
    cur = None
    # Set up tex file
    if (tex_file):
        print("\\documentclass{standalone}", file=tex_file)
        # print("\\usepackage{longtable}", file=tex_file)
        print("\\begin{document}", file=tex_file)
        # print("\\begin{longtable}", file=tex_file)
        if (incl_calcs is not None): # select only included calcs
            calcs = set([c for c in calcs if ci_in(c, incl_calcs)])
        print("\\begin{tabular}{"+'|'.join(['c']*(len(calcs)+1))+"}",
              file=tex_file)
        print("Metric & "+' & '.join([c for c in sorted(calcs) if not
                                      ci_eq(c, PERC_N)])+"\\\\",
              file=tex_file)
    for (mode, metric) in zipped:
        # check if this metric and mode should be displayed
        if ((incl_metrics is None or ci_in(metric, incl_metrics)) and
            (ci_eq(mode, 'base') or flitsrs is None or ci_in(metric, flitsrs)) and
            (ci_in(mode, avgs) and ci_in(metric, avgs[mode]))):
            if (ci_eq(group, 'metric')):
                if (metric != cur):
                    print_heading(metric, 0)
                    cur = metric
                print_heading(mode, 1)
            else:
                if (mode != cur):
                    print_heading(mode, 0)
                    cur = mode
                print_heading(metric, 1)
            if (tex_file):
                print_tex_heading(mode, metric)
            print_results(mode, metric)
    if (tex_file):
        print("\\end{tabular}", file=tex_file)
        # print("\\end{longtable}", file=tex_file)
        print("\\end{document}", file=tex_file)


if __name__ == "__main__":
    class RecurseAction(Action):
        def __init__(self, option_strings, dest, nargs=None, **kwargs):
            super().__init__(option_strings, dest, nargs, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, True)
            if (values is not None):
                setattr(namespace, 'max', values)

    met_names = Suspicious.getNames(True)

    parser = ArgumentParser(prog='merge', description='Merge .results files '
                            'produced by the run_all script')
    parser.add_argument('-R', '--relative', action='store_true', help='Compute '
                        'relative values instead of absolute values')
    parser.add_argument('-r', '--recurse', nargs='?', type=int, default=False,
                        action=RecurseAction, metavar='X', help='Activates '
                        'the scripts recursive mode. This makes the script '
                        'recursively look in sub-directories of the current '
                        'directory for results files. An optional maximum '
                        'recurse limit X can be given.')
    parser.add_argument('-i', '--incl', nargs='+', metavar='DIR_NAME',
                        action='extend', default=[],
                        help='Specifies particular directories to include for '
                        'the recursive option. May be specified multiple times')
    parser.add_argument('-e', '--excl', nargs='+', metavar='DIR_NAME',
                        action='extend', default=[],
                        help='Specifies particular directories to exclude for '
                        'the recursive option. May be specified multiple times')
    parser.add_argument('-t', '--tex', nargs='?', const='results.tex', metavar='FILE',
                        type=FileType('w'), help='Specifies that an additional '
                        'output file should be generated that contains the '
                        'results in a LaTeX table (in .tex format). By default '
                        'this is stored in results.tex, but an optional '
                        'filename FILE may be given')
    parser.add_argument('-p', '--perc@n', nargs='?', const='perc_at_n_results',
                        type=FileType('w'), metavar='FILE', help='Specifies '
                        'that an additional output file should be generated '
                        'that contains the percentage-at-n results. By default '
                        'this is stored in perc_at_n_results, but an optional '
                        'filename FILE may be given', dest='perc_at_n',
                        default='perc_at_n_results')
    parser.add_argument('-1', '--inline-perc@n', action='store_const',
                        const=None, dest='perc_at_n', help='Instead of '
                        'producing a separate percentage-at-n file, place the '
                        'results inline in the results file')
    parser.add_argument('-o', '--output', action='store', type=FileType('w'),
                        metavar='FILE', help='Store the results in the file '
                        'with filename FILE. By default the name "results" is '
                        'used', default='results')
    parser.add_argument('-d', '--decimals', action='store', type=int, default=24,
                        help='Sets the precision (number of decimal points) '
                        'for the output of all of the calculations Does not '
                        'impact percentage-at-n values. (default %(default)s, '
                        'i.e. all python-stored significance).')
    parser.add_argument('-g', '--grouping-order', choices=['metric', 'type'],
                        default='metric', dest='group',
                        help='Specifies the way in which the output should be '
                        'grouped. "metric" groups first by metrics and then by '
                        'types, "type" does the opposite (default %(default)s)')
    parser.add_argument('-c', '--calcs', nargs='+', metavar='CALC',
                        help='Specify the list of calculations to include when '
                        'merging. By default all available calculations are '
                        'included. NOTE: the names of the calculations need to '
                        'be found in the corresponding .results files')
    parser.add_argument('--percentage', nargs='+', metavar='CALC',
                        help='Specify calculations that must be intepreted as '
                        'a percentage value. NOTE: the names of the '
                        'calculations need to be found in the corresponding '
                        '.results files')
    parser.add_argument('-s', '--significance', nargs='?', const='type',
                        choices=['metric', 'type'], dest='sign',
                        help='Specifies that additional significance tests '
                        'should be performed to test the differences in '
                        'results. The significance tests will either be '
                        'conducted between metrics of the same type [metric] '
                        'or between types using the same metric [type] '
                        '(default %(const)s). If type is given, and the '
                        '--tex option is also used, significance indicators '
                        'will be added to the TeX output indicating advanced '
                        'types significantly greater than their baselines '
                        '(see --less-significance for significantly less)')
    parser.add_argument('-f', '--flitsrs', nargs='+', metavar='METRIC',
                        help='Specify the metrics for which to display FLITSR '
                        'and FLITSR* values for. By default all metric\'s '
                        'FLITSR and FLITSR* values are shown.',
                        choices=met_names)
    parser.add_argument('-m', '--metrics', nargs='+', metavar='METRIC',
                        help='Specify the metrics to merge results for. By '
                        'default all metrics that appear in filenames of found '
                        'files will be merged. Note that this option only '
                        'restricts the output, all files available are still '
                        'read, however files not existing are not read.',
                        choices=met_names)
    parser.add_argument('-l', '--less-significance', nargs='+', metavar='CALC',
                        help='Intended for use with the --significance and '
                        '--tex options. Specify the calculations whose result '
                        'is to be tested for significantly less than the '
                        'baseline instead of significantly greater, which is '
                        'the default. Affects the significance indicators '
                        'for the TeX output. NOTE: the names of the '
                        'calculations need to be found in the corresponding '
                        '.results files', dest='sign_less', default=[])
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if ('max' not in args):
        args.max = None
    if (args.perc_at_n is None):
        args.perc_at_n = args.output
    # Remove trailing '/' for included and excluded dirs
    args.incl = list(map(lambda s: str.rstrip(s, '/'), args.incl))
    args.excl = list(map(lambda s: str.rstrip(s, '/'), args.excl))
    merge(args.recurse, args.max, args.incl, args.excl, args.relative,
          args.output, args.perc_at_n, args.tex, dec=args.decimals,
          group=args.group, incl_calcs=args.calcs, percs=args.percentage,
          incl_metrics=args.metrics, flitsrs=args.flitsrs, sign=args.sign,
          sign_less=args.sign_less)
