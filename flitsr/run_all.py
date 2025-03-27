from multiprocessing import Pool
from typing import List, Optional, Set, Any, Iterator
from types import ModuleType
from collections.abc import Callable
import importlib
import sys
import os
from pathlib import Path
import shutil
import time
from fnmatch import fnmatch
import re
from contextlib import redirect_stderr
import random
from enum import Enum, auto

import argparse
import argcomplete

from flitsr.suspicious import Suspicious


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
                (empty is None or empty == (os.path.getsize(filename) == 0))):
                path = os.path.join(root, filename)
                # Check for action
                if (action is not None):
                    yield action(path)
                else:
                    yield path


def natsort(s, _nsre=re.compile(r'(\d+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]


class Runall:
    def __init__(self, metrics: Set[str], num_cpus: Optional[int] = None,
                 recover: bool = False, flitsr_args: List[str] = None,
                 driver: Optional[ModuleType] = None):
        self.num_inputs = -1  # Progress bar counter
        if (driver is None):
            driver = importlib.import_module('flitsr')
        self.driver = driver
        self.num_cpus = num_cpus
        # set up the args
        self.args = ["--all"]
        for metric in metrics:
            self.args.extend(["-m", metric])
        self.recover = recover
        if (recover):
            self.args.append("--no-override")
        if (flitsr_args is not None):
            for arg in flitsr_args:
                self.args.extend(arg.split())

    def run_flitsr(self, input_cov: str):
        args = self.args + [input_cov]
        with open(input_cov+".err", 'w') as errfile:
            with redirect_stderr(errfile):
                for i in range(10):
                    print(input_cov, file=sys.stderr)
                    time.sleep(random.random())
                self.driver.main(args)

    def progress(self, cur):
        size = shutil.get_terminal_size().columns - 7
        perc = int((cur * 100) / self.num_inputs)
        nfill = int((cur * size) / self.num_inputs)
        nempty = size - nfill
        print(f'[{u'█'*nfill}{' '*nempty}] {perc:3d}%', end='\r')
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
                             depth=depth, action=os.path.dirname)
        elif (input_type == InputType.TCM):
            if (ext is None):  # Sanity check
                ext = '*'
            inputs_us = find('.', type='f', name="*."+ext, excl_dirs=exclude,
                             incl_dirs=include, depth=depth)
        else:
            inputs_us = find('.', excl_dirs=exclude, incl_dirs=include,
                             depth=depth)
        inputs = sorted(inputs_us, key=natsort)
        dirs = {os.path.dirname(f) for f in inputs}

        # save base directory
        basedir = Path(os.curdir).absolute()

        if (not self.recover and os.path.isfile("results.err")):
            os.remove("results.err")

        # Iterate over each directory
        for dir_ in dirs:
            print(f'Running {dir_.removeprefix("./")}')
            os.chdir(dir_)
            if (self.recover and os.path.isfile("results")):
                print(f'Recovered {dir_.removeprefix("./")}, skipping...')
                os.chdir(basedir)
                continue
            elif (not self.recover and os.path.isfile("done_inputs.tmp")):
                os.remove("done_inputs.tmp")
            proj_inp = list(map(os.path.basename, [i for i in inputs if
                                                   i.startswith(dir_+"/")]))
            self.num_inputs = len(proj_inp)
            # start worker processes
            self.progress(0)
            with Pool(processes=self.num_cpus) as pool:
                for i, _ in enumerate(pool.imap_unordered(self.run_flitsr,
                                                          proj_inp), 1):
                    self.progress(i)
            self.progress(self.num_inputs)


def main(argv: List[str]):
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

    parser.add_argument('-i', '--include', metavar='dir', action='append',
                        help='Include directories named <dir> in run (can be '
                        'specified multiple times)')
    parser.add_argument('-e', '--exclude', metavar='dir', action='append',
                        help='Exclude directories names <dir> in run (can be '
                        'specified multiple times')

    parser.add_argument('-d', '--depth', action='store', help='Specifies the '
                        'depth at which to look for inputs')
    parser.add_argument('-t', '--tcm', metavar='extension', nargs='?',
                        default=None, const='*', help='Look only for TCM type '
                        'inputs (with optional extension <extension>)')
    parser.add_argument('-g', '--gzoltar', action='store_true', help='Look '
                        'only for GZoltar type inputs')

    parser.add_argument('-c', '--num-cores', metavar='cores', type=int,
                        help='Sets the number of cores to run in parallel on '
                        '(default automatic)')
    parser.add_argument('-r', '--recover', action='store_true', help='Recover '
                        'from a partial run_all run by re-using existing files')
    parser.add_argument('-a', '--flitsr_arg', nargs='+', action='extend',
                        help='Specify an argument to give to the flitsr program')
    parser.add_argument('-p', '--driver', help='Specify an alternate flitsr '
                        'driver to use for running')

    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    # Process metrics
    metrics = set(args.metrics or Suspicious.getNames())
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

    # Process driver
    driver = None
    if (args.driver is not None):
        try:
            driver = importlib.import_module('flitsr.'+args.driver)
        except ModuleNotFoundError:
            parser.error(f"Driver {args.driver} is not a valid flitsr driver")

    run_all = Runall(metrics, num_cpus=args.num_cores, recover=args.recover,
                     flitsr_args=args.flitsr_args, driver=driver)
    run_all.run(inp_type, include=args.include, exclude=args.exclude,
                depth=args.depth, ext=args.tcm)


if __name__ == '__main__':
    main(sys.argv)
