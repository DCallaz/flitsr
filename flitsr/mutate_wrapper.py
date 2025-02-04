from flitsr.universalmutator import genmutants, analyze
from flitsr.spectrum import Spectrum
from flitsr import errors
from flitsr.ranking import Ranking
from typing import List, Tuple, Set
from os import path as osp
from io import StringIO
from contextlib import redirect_stdout
import subprocess as sp
import os
import shutil
import sys
import re
import glob


class Mutation:
    def __init__(self, test_cmd: str, spectrum: Spectrum,
                 compile_cmd: str = None, srcdir: str = '**/',
                 method_lvl: bool = False):
        self.spectrum = spectrum
        self._mutant_dir = osp.join(osp.curdir, 'mutants')
        os.makedirs(self._mutant_dir, exist_ok=True)
        self._test_cmd = test_cmd
        self._srcdir = srcdir
        self._method_lvl = method_lvl
        self._compile_cmd = compile_cmd
        initial_ts = sp.run(test_cmd, text=True, shell=True,
                            capture_output=True)
        self._failing_tests = self._parse_mutant(initial_ts.stdout)

    def filter_ranking(self, ranking: Ranking, cutoff=10):
        """
        Filter the given ranking based on mutation results to push up
        suspicious elements and push down unsuspicious elements according to
        the mutation results. By default, only the top 10 elements will be
        filtered, however this can be altered by setting `cutoff`. Setting
        `cutoff` to -1 will enable filtering of the entire ranking.
        """
        r_iter = iter(ranking)
        try:
            for i in range(cutoff):
                rank = next(r_iter)
                for elem in rank.group.get_elements():
                    results = self.mutate_element(elem)
        except StopIteration:
            pass

    def mutate_element(self, elem: Spectrum.Element) -> List[Tuple[int, int]]:
        """ Mutate a single element from the spectrum, and return results """
        # Get the source file
        if (osp.isfile(elem.path)):
            srcfile = elem.path
        elif (osp.isfile(osp.join(self._srcdir, elem.path))):
            srcfile = osp.join(self._srcdir, elem.path)
        else:
            files = glob.glob(osp.join(self._srcdir, re.sub('\\.', '/',
                                                            elem.path)+'.*'),
                              recursive=True)
            if (len(files) == 0):
                raise FileNotFoundError(f'Cannot find element "{elem}"')
            elif (len(files) > 1):
                errors.warning("Found more than one file for element", elem)
            # Take the shortest file name as the closest match
            srcfile = sorted(files, key=lambda x: len(x))[0]
        # Specify the lines
        if (self._method_lvl):
            raise NotImplementedError("Method level not implemented for mutation")
        if (elem.line is None):
            raise ValueError(f'Line number for element "{elem}" needed for mutation')
        with open('lines', 'w') as line_file:
            line_file.write(str(elem.line))
        # Mutate the element
        try:
            sys.argv = ['mutate', srcfile, '--noCheck', '--lines', 'lines',
                        '--mutantDir', self._mutant_dir]
            with redirect_stdout(StringIO()):
                genmutants.main()
        except SystemExit:
            pass
        # Analyze mutants
        try:
            sys.argv = ['analyze_mutants', srcfile, self._test_cmd,
                        '--verbose', '--mutantDir', self._mutant_dir]
            # Add compile command if available
            if (self._compile_cmd is not None):
                sys.argv.extend(['--numMutants', '100', '--compileCommand',
                                 self._compile_cmd])
            with redirect_stdout(stdout_results := StringIO()):
                analyze.main()
        except SystemExit:
            pass
        # Parse the results
        results = self._parse_results(stdout_results)
        self._clean_up(srcfile)
        return results

    def _parse_results(self,
                       stdout_results: StringIO) -> List[Tuple[int, int]]:
        stdout_results_str = stdout_results.getvalue()
        print(stdout_results_str)
        mutants = re.split('=+\n', stdout_results_str)
        # print("num mutants:", len(mutants))
        results = []
        for mutant in mutants:
            try:
                failing_tests = self._parse_mutant(mutant)
                fail_pass = len(self._failing_tests.difference(failing_tests))
                pass_fail = len(failing_tests.difference(self._failing_tests))
                results.append((fail_pass, pass_fail))
            except StopIteration:
                continue
        return results

    def _parse_mutant(self, mutant: str) -> Set[Spectrum.Test]:
        mutant_lines = mutant.splitlines()
        start = next(i for i in range(len(mutant_lines))
                     if mutant_lines[i].startswith("Failing tests"))+1
        i = 0
        failing_tests = set()
        while (start+i < len(mutant_lines) and
               (m := re.match('\\s*-\\s+(.+)', mutant_lines[start+i]))):
            tests = self.spectrum.search_tests(m.group(1).replace('::', '#'))
            if (len(tests) != 1):
                raise ValueError(f'Could not find unique test "{m.group(1)}"')
            failing_tests.add(tests[0])
            i += 1
        return failing_tests

    def _clean_up(self, srcfile):
        shutil.rmtree('mutants')
        for umbackup in glob.glob(srcfile+'*um.backup*'):
            os.remove(umbackup)
