# PYTHON_ARGCOMPLETE_OK
import re
from flitsr.percent_at_n import combine
import os
import sys
from os import path as osp
from io import TextIOWrapper
from scipy.stats import wilcoxon
from argparse import ArgumentParser, Action, FileType, ArgumentTypeError
import argcomplete
from flitsr.file import File
from flitsr.suspicious import Suspicious
from typing import Set, Dict, List, Tuple, Collection, Optional

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
        # if number of observations differ, no significance
        if (len(self.all) != len(avg.all)):
            return ('equal', 1.0)
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


def find_dirs(dirs: List[str], path, depth=1, max=None,
              incl=Dict[str, List[str]], excl=Dict[str, List[str]]):
    """
    Recursively traverse a directory structure at the given `path` and find
    directories containing results files, adding them to `dirs`. An optional
    maximum depth may be given, along with names to include and exclude at
    various depth levels ("*" indicates any level).
    """
    # Get the names to include and exclude at this depth level
    incl_lvl = incl.get(str(depth), []) + incl.get("*", [])
    excl_lvl = excl.get(str(depth), []) + excl.get("*", [])
    for dir in os.scandir(path):
        if (dir.is_dir() and (dir.name not in excl_lvl) and
            (len(incl_lvl) == 0 or dir.name in incl_lvl)):
            new_path = dir.path
            if ((max and depth >= max) or
                (not max and any(f.endswith('.results') for f in
                                 os.listdir(new_path)))):
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


def merge(recurse: bool, max: int, incl: List[Tuple[str, str]],
          excl: List[Tuple[str, str]], rel: bool,
          output_file: TextIOWrapper, perc_file: TextIOWrapper,
          tex_file: TextIOWrapper, dec=2, group='metric', incl_calcs=None,
          percs=None, incl_metrics=None, flitsrs=None, sign=None,
          sign_less=[], base_type=None, thrs=[], keep_order=False):
    # Set up the include and exclude dir names dicts
    incl_dict: Dict[str, List[str]] = {}
    excl_dict: Dict[str, List[str]] = {}
    for d, n in incl:
        incl_dict.setdefault(d, []).append(n)
    for d, n in excl:
        excl_dict.setdefault(d, []).append(n)
    # set up other variables
    if (base_type is None):
        base_type = 'base'
    temp_metrics: Set[str] = set()
    modes: Set[str] = set()
    temp_calcs: Set[str] = set()
    #           dir       mode      metric
    files: Dict[str, Dict[str, Dict[str, File]]] = {}
    #          mode      metric    calc
    avgs: Dict[str, Dict[str, Dict[str, Avg]]] = {}
    if (rel):
        if (not recurse):
            size = int(open("../size").readline())
    # Find the directories and results files
    dirs = [""]
    if (recurse):
        dirs = []
        find_dirs(dirs, ".", max=max, incl=incl_dict, excl=excl_dict)
    # Read in all results
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
                temp_metrics.add(metric)
                files[d].setdefault(mode, {})[metric] = File(file)
                avgs.setdefault(mode, {}).setdefault(metric, {})
        if (rel):
            sizes[d] = int(open(osp.join(d, "../size")).readline())

    # Collect all the results
    for d in dirs:
        for mode in modes:
            for metric in temp_metrics:
                try:
                    block = readBlock(files[d][mode][metric])
                except Exception:
                    print('WARNING: Could not find results for '
                          f'{mode.replace("_", " ").title()} '
                          f'{metric.replace("_", " ").title()} in dir {d}',
                          file=sys.stderr)
                    continue
                while (block != []):
                    for line in block:
                        line_s = line.split(": ")
                        calc = line_s[0]
                        temp_calcs.add(calc)
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
    # calculate thresholds
    for thr in thrs:
        thr_key = str(thr).lower()
        temp_calcs.add(thr_key)
        for mode in modes:
            for metric in temp_metrics:
                vals = avgs[mode][metric][thr.calc].all
                count = 0.0
                for val in vals:
                    if (thr.comp(val, thr.threshold)):
                        count += 1
                avgs[mode][metric][thr_key] = Avg()
                avgs[mode][metric][thr_key].adds = len(vals)
                avgs[mode][metric][thr_key].all = [count]
    # select only included calcs
    if (incl_calcs is not None):
        # preserves the order of calcs from cmd line
        calcs = [c for c in incl_calcs if ci_in(c, temp_calcs)]
    else:
        calcs = list(temp_calcs)
    # select only included metrics
    if (incl_metrics is not None):
        # preserves the order of metrics from cmd line
        metrics = [m for m in incl_metrics if ci_in(m, temp_metrics)]
    else:
        metrics = list(temp_metrics)
    # sort metrics or keep cmd line order
    if (not keep_order):
        calcs = sorted(calcs)
        metrics = sorted(metrics)

    def print_heading(name, tabs):
        name_disp = name.replace("_", " ").title()
        print('\t'*tabs, name_disp, sep='', file=output_file)
        if (ci_in(PERC_N, calcs) and perc_file is not None and
                perc_file != output_file):
            print('\t'*tabs, name_disp, sep='', file=perc_file)

    def print_tex_heading(mode, metric):
        metric_disp = metric.replace("_", " ").title()
        mode_disp = mode.replace("_", " ").title()
        print('%25s' % (metric_disp + " " + mode_disp), end=" & ",
              file=tex_file)

    def print_results(mode, metric):
        for j, calc in enumerate(calcs):
            if (ci_eq(calc, PERC_N)):
                if (perc_file is not None):
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
                    base = base_type.format(re.sub('_[^_]*$', '', mode))
                    if (sign == 'type' and not ci_eq(mode, base)):
                        try:
                            r, p = avg.significance(
                                    avgs[base][metric][calc])
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
        zipped = [(mo, me) for me in metrics for mo in sorted(modes)]
    else:
        zipped = [(mo, me) for mo in sorted(modes) for me in metrics]
    cur = None
    # Set up tex file
    if (tex_file):
        print("\\documentclass{standalone}", file=tex_file)
        # print("\\usepackage{longtable}", file=tex_file)
        print("\\begin{document}", file=tex_file)
        # print("\\begin{longtable}", file=tex_file)
        print("\\begin{tabular}{"+'|'.join(['c']*(len(calcs)+1))+"}",
              file=tex_file)
        print("Metric & "+' & '.join([c for c in calcs if not
                                      ci_eq(c, PERC_N)])+"\\\\",
              file=tex_file)
    for (mode, metric) in zipped:
        # check if this mode should be displayed
        if ((ci_eq(mode, 'base') or flitsrs is None or ci_in(metric, flitsrs))
            and (ci_in(mode, avgs) and ci_in(metric, avgs[mode]))):
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


def parse_dir_arg(dir_arg: str) -> Tuple[str, str]:
    """
    Parses a given directory argument of the form '[<depth>:]<dir name>',
    where the depth is optional. NOTE: the directory name must not include the
    colon character (':') as this is used to separate the depth.

    Returns a tuple with the depth at which the argument applies, and the
    directory name.
    """
    if (":" in dir_arg):
        depth, _, dir_name = dir_arg.partition(":")
        if (depth != "*" and not depth.isdigit()):
            raise ArgumentTypeError(f'Depth \"{depth}\" not an integer')
    else:
        depth = "*"
        dir_name = dir_arg
    return (depth, dir_name.rstrip('/'))


def above(val, threshold):
    return val >= threshold


def below(val, threshold):
    return val <= threshold


class Threshold:
    def __init__(self, calc, comp, threshold):
        self.calc = calc
        self.comp = comp
        self.threshold = threshold

    def __getitem__(self, i):
        if (i == 0):
            return self.calc
        elif (i == 1):
            return self.comp
        elif (i == 2):
            return self.threshold
        else:
            IndexError("tuple index out of range")

    def __str__(self):
        return f'threshold ({self.calc}, {self.comp.__name__}, {self.threshold})'


def main(argv: Optional[List[str]] = None):
    class RecurseAction(Action):
        def __init__(self, option_strings, dest, nargs=None, **kwargs):
            super().__init__(option_strings, dest, nargs, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, True)
            if (values is not None):
                setattr(namespace, 'max', values)

    class ThresholdAction(Action):
        def __call__(self, parser, args, values, option_string=None):
            # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)
            calc, comp, threshold = values
            if not ci_in(comp, ('above', 'below')):
                raise ValueError('invalid Comparison {s!r}'.format(s=comp))
            else:
                comp = eval(comp)
            threshold = float(threshold)
            if (not hasattr(args, self.dest) or
                    getattr(args, self.dest) is None):
                setattr(args, self.dest, list())
            d = getattr(args, self.dest)
            d.append(Threshold(calc, comp, threshold))

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
    parser.add_argument('-i', '--incl', nargs='+', metavar='DIR_ARG',
                        action='extend', default=[], type=parse_dir_arg,
                        help='Specifies particular directories to include for '
                        'the recursive option. You may optionally give a '
                        'depth with each directory in the format '
                        'DIR_ARG=\"[<depth>:]<dir name>\", where the depth is an '
                        'integer starting with 1 (the current directory). '
                        'By default a depth of \"*\" is used, indicating any '
                        'depth is valid. NOTE: the colon character (\":\") '
                        'should not appear in the directory name, but if it '
                        'must, then the depth must also be given. This option '
                        'may be specified multiple times')
    parser.add_argument('-e', '--excl', nargs='+', metavar='DIR_ARG',
                        action='extend', default=[], type=parse_dir_arg,
                        help='Specifies particular directories to exclude for '
                        'the recursive option. You may optionally give a '
                        'depth with each directory (see --incl for format).'
                        'This option may be specified multiple times')
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
                        'filename FILE may be given', dest='perc_at_n')
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
    parser.add_argument('--threshold', nargs=3, action=ThresholdAction, default=[],
                        help='Format: --threshold <calculation> {above, below} '
                        '<float>. Specifies that an additional calculation '
                        'should be added that counts the number of versions '
                        'where the given calculation is above or below the '
                        'given float threshold. The calculations are the same '
                        'as for the --calcs argument.')
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
                        '(see --base-type for changing the baseline, and '
                        '--less-significance for significantly less)')
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
    parser.add_argument('-b', '--base-type', help='Intended for use with '
                        '--significance and --tex options. Specify the base '
                        'type that will be compared against for all other '
                        'types when adding significance test annotations to '
                        'the TeX output. Use the format "{}_<type>" if the '
                        'baseline to compare to is dependant on the type.')
    parser.add_argument('-k', '--keep-order', action='store_true',
                        help='Instead of sorting the metrics and calculations '
                        'by alphabetical order, keep the order that the are '
                        'specified on the command line by the -m and -c '
                        'options. This option does nothing to the '
                        'corresponding order if either of those options are '
                        'unspecified')
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    if ('max' not in args):
        args.max = None
    merge(args.recurse, args.max, args.incl, args.excl, args.relative,
          args.output, args.perc_at_n, args.tex, dec=args.decimals,
          group=args.group, incl_calcs=args.calcs, percs=args.percentage,
          incl_metrics=args.metrics, flitsrs=args.flitsrs, sign=args.sign,
          sign_less=args.sign_less, base_type=args.base_type,
          thrs=args.threshold, keep_order=args.keep_order)


if __name__ == "__main__":
    main()
