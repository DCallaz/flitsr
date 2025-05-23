# PYTHON_ARGCOMPLETE_OK
from multiprocessing import Pool
from typing import List, Optional, Set, Any, Iterator, Callable, Optional
import importlib
from importlib.util import find_spec
import sys
import os
from os import path as osp
from pathlib import Path
import shutil
from fnmatch import fnmatch
import re
from contextlib import redirect_stderr, redirect_stdout
from enum import Enum, auto

import argparse
import argcomplete

from flitsr.suspicious import Suspicious
from flitsr import merge
from flitsr.errors import warning


class InputType(Enum):
    GZOLTAR = auto()
    TCM = auto()
    DEPTH = auto()


def find(directory: str, type: Optional[str] = None,
         name: Optional[str] = None, empty: Optional[bool] = None,
         excl_dirs: Optional[List[str]] = None,
         incl_dirs: Optional[List[str]] = None,
         depth: Optional[int] = None,
         action: Optional[Callable[[str], Any]] = None) -> Iterator[Any]:
    """ Mimicks the bash-equalivalent find command on linux. """
    for root, dirs, files in os.walk(directory):
        rootp = Path(root)
        # Stop looking if the depth has been reached
        if (depth is not None and len(rootp.parts) != depth):
            continue
        # check for included/excluded dirs
        if ((excl_dirs is not None and
             any(d in rootp.parts for d in excl_dirs)) or
            (incl_dirs is not None and
             all(d not in rootp.parts for d in incl_dirs))):
            continue
        to_check = (dirs+files if (type is None) else dirs if (type == 'd')
                    else files if (type == 'f') else [])
        for filename in to_check:
            # check the name and emptiness
            if ((name is None or fnmatch(filename, name)) and
                (empty is None or empty == (osp.getsize(filename) == 0))):
                path = osp.join(root, filename)
                # Check for action
                if (action is not None):
                    yield action(path)
                else:
                    yield path


def removeprefix(string : str, prefix: str):
    if (prefix and string.startswith(prefix)):
        return string[len(prefix):]
    return string

def removesuffix(string: str, suffix: str):
    if (suffix and string.endswith(suffix)):
        return string[:-len(suffix)]
    return string


def natsort(s, _nsre=re.compile(r'(\d+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]


class Runall:
    def __init__(self, metrics: Set[str], num_cpus: Optional[int] = None,
                 recover: bool = False, flitsr_args: List[str] = None,
                 driver: Optional[str] = None):
        self.num_inputs = -1  # Progress bar counter
        if (driver is None):
            driver = 'main'
        self.driver = driver
        self.num_cpus = num_cpus
        self.metrics = metrics
        self.recover = recover
        # set up the args
        self.args = ["--all"]
        for metric in metrics:
            self.args.extend(["-m", metric])
        if (recover):
            self.args.append("--no-override")
        if (flitsr_args is not None):
            for arg in flitsr_args:
                self.args.extend(arg.split())

    def run_flitsr(self, input_cov: str):
        args = self.args + [input_cov]
        with open(input_cov+".err", 'w') as errfile:
            with redirect_stderr(errfile):
                driver = importlib.import_module('flitsr.'+self.driver)
                try:
                    driver.main(args)
                except SystemExit:
                    pass
        with open("done_inputs.tmp", 'a') as done:
            print(input_cov, file=done)

    def progress(self, cur):
        size = shutil.get_terminal_size().columns - 7
        perc = int((cur * 100) / self.num_inputs)
        nfill = int((cur * size) / self.num_inputs)
        nempty = size - nfill
        bar = u'\u2588'
        print(f'[{bar*nfill}{" "*nempty}] {perc:3d}%', end='\r')
        if (cur == self.num_inputs):
            print()

    def run(self, input_type: InputType, include: List[str] = [],
            exclude: List[str] = [], depth: Optional[int] = None,
            ext: Optional[str] = None):
        def del_tell(file: str):
            os.remove(file)
            print(f'Deleting empty results file: {file}\n')
        # Firstly delete all empty results
        find('.', type='f', name='*results*', empty=True, action=del_tell)
        # Also delete all empty runs, as this could cause problems for recover
        find('.', type='f', name="*.run", empty=True, action=del_tell)

        # get inputs
        if (input_type == InputType.GZOLTAR):
            inputs_us = find('.', type='f', name="spectra.csv",
                             excl_dirs=exclude, incl_dirs=include,
                             depth=depth, action=osp.dirname)
        elif (input_type == InputType.TCM):
            if (ext is None):  # Sanity check
                ext = '*'
            inputs_us = find('.', type='f', name="*."+ext, excl_dirs=exclude,
                             incl_dirs=include, depth=depth)
        else:
            inputs_us = find('.', excl_dirs=exclude, incl_dirs=include,
                             depth=depth)
        inputs = sorted(inputs_us, key=natsort)
        dirs_us = {osp.dirname(f) for f in inputs}
        dirs = sorted(dirs_us, key=natsort)

        # save base directory
        basedir = Path(os.curdir).absolute()

        if (not self.recover and osp.isfile("results.err")):
            os.remove("results.err")

        # Iterate over each directory
        for dir_ in dirs:
            # Initial housekeeping
            print(f'Running {removeprefix(dir_, "./")}')
            os.chdir(dir_)
            done_inp = []
            if (self.recover and osp.isfile("results")):
                print(f'Recovered {removeprefix(dir_, "./")}, skipping...')
                os.chdir(basedir)
                continue
            elif (not self.recover and osp.isfile("done_inputs.tmp")):
                os.remove("done_inputs.tmp")
            elif (self.recover and osp.isfile("done_inputs.tmp")):
                done_inp = list(map(str.strip,
                                    open("done_inputs.tmp").readlines()))
                if (len(done_inp) > 0):
                    print('Skipping done inputs:')
                    print(*done_inp, sep=", ")
            proj_inp = list(map(osp.basename, [i for i in inputs if
                                               i.startswith(dir_+"/")]))
            self.num_inputs = len(proj_inp)
            # Remove done inputs
            proj_inp = sorted(set(proj_inp) - set(done_inp), key=natsort)
            # start worker processes
            self.progress(len(done_inp))
            with Pool(processes=self.num_cpus) as pool:
                for i, _ in enumerate(pool.imap_unordered(self.run_flitsr,
                                                          proj_inp),
                                      len(done_inp)+1):
                    self.progress(i)
            # clean up after running flitsr
            # print out the error files
            with redirect_stdout(open(osp.join(basedir, "results.err"), 'a')):
                err_files = sorted(find('.', type='f', name="*.err", depth=0),
                                   key=natsort)
                for error_file in err_files:
                    if (osp.basename(error_file) != "results.err"):
                        if (osp.getsize(error_file) > 0):
                            print_err = (removesuffix(removeprefix(
                                error_file, "./"), ".err"))
                            print(f'Dir {removeprefix(dir_, "./")}',
                                  f'File {print_err}')
                            with open(error_file) as file:
                                print(file.read(), end='')
                        os.remove(error_file)
            # collect the results files
            for m in self.metrics:
                rs = find('.', type='f', name='*.run')
                tre = f"\\.\\/(.*)_{m}_.+\\.run"
                try:
                    types = {m.group(1) for m in (re.match(tre, r) for r in rs)
                             if m is not None}
                except AttributeError:
                    warning("Could not collect types")
                    pass
                for t in sorted(types, key=natsort):
                    with redirect_stdout(open(f'{t}_{m}.results', 'w')):
                        runs = sorted(find('.', type='f', depth=0,
                                           name=f'{t}_{m}_*.run'), key=natsort)
                        for run in runs:
                            orig = removeprefix(run, f'./{t}_{m}_')
                            print(orig)
                            with open(run) as file:
                                print(file.read(), end='')
                            os.remove(run)
                            print("--------------------------")
            merge.main([])
            os.remove("done_inputs.tmp")
            print(f'Done in {removeprefix(dir_, "./")}')
            os.chdir(basedir)
        # Check for empty results file
        results_fl = osp.join(basedir, "results.err")
        if (os.path.isfile(results_fl) and os.path.getsize(results_fl) == 0):
            os.remove(results_fl)


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(prog='run_all', description='Run large '
                                     'experiments automatically')

    metric_names = Suspicious.getNames(True)
    parser.add_argument('-m', '--metrics', metavar='METRIC', action='extend',
                        nargs='+', help='Runs only the given metrics (can be '
                        'specified multiple times)', choices=metric_names)
    parser.add_argument('-M', '--exclude-metrics', metavar="METRIC",
                        action='extend', nargs='+', help='Excludes the given '
                        'metrics (can be specified multiple times)',
                        choices=metric_names)

    parser.add_argument('-i', '--include', metavar='DIR', action='append',
                        help='Include directories named DIR in run (can be '
                        'specified multiple times)')
    parser.add_argument('-e', '--exclude', metavar='DIR', action='append',
                        help='Exclude directories names DIR in run (can be '
                        'specified multiple times)')

    parser.add_argument('-d', '--depth', action='store', help='Specifies the '
                        'depth at which to look for inputs', type=int)
    parser.add_argument('-t', '--tcm', metavar='EXT', nargs='?',
                        default=None, const='*', help='Look only for TCM type '
                        'inputs (with optional extension EXT)')
    parser.add_argument('-g', '--gzoltar', action='store_true', help='Look '
                        'only for GZoltar type inputs')

    parser.add_argument('-c', '--num-cpus', metavar='CPUS', type=int,
                        help='Sets the number of CPUs to run in parallel on '
                        '(default automatic)')
    parser.add_argument('-r', '--recover', action='store_true', help='Recover '
                        'from a partial run_all run by re-using existing '
                        'files')
    parser.add_argument('-a', '--flitsr_arg', nargs='+', action='extend',
                        help='Specify an argument to give to the flitsr '
                        'program. NOTE: use -a="<argument>" syntax for '
                        'arguments beginning with a dash ("-")')
    parser.add_argument('-p', '--driver', help='Specify an alternate flitsr '
                        'driver to use for running')

    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    # Process incl & excl (remove trailing slashes)
    if (args.include is not None):
        args.include = [path.rstrip('/') for path in args.include]
    if (args.exclude is not None):
        args.exclude = [path.rstrip('/') for path in args.exclude]

    # Process metrics
    metrics = set(args.metrics or Suspicious.getNames())
    if (args.exclude_metrics is not None):
        metrics.difference_update(args.exclude_metrics)

    # Process input type
    if (args.gzoltar):
        inp_type = InputType.GZOLTAR
    elif (args.tcm is not None):
        inp_type = InputType.TCM
    elif (args.depth is not None):
        inp_type = InputType.DEPTH
    else:
        parser.error("Please specify a depth or input type")

    # check if driver exists
    if (args.driver is not None):
        spec = find_spec('flitsr.'+args.driver)
        if (spec is None):
            print("ERROR")
            parser.error(f"Driver {args.driver} is not a valid flitsr driver")
            quit()

    run_all = Runall(metrics, num_cpus=args.num_cpus, recover=args.recover,
                     flitsr_args=args.flitsr_arg, driver=args.driver)
    run_all.run(inp_type, include=args.include, exclude=args.exclude,
                depth=args.depth, ext=args.tcm)


if __name__ == '__main__':
    main()
