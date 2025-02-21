from flitsr.universalmutator import genmutants, analyze
from flitsr.spectrum import Spectrum
from flitsr import errors
from flitsr.ranking import Ranking
from flitsr.suspicious import Suspicious
from typing import List, Set, Dict, Optional
from collections.abc import Callable
from os import path as osp
from io import StringIO
from contextlib import redirect_stdout
import subprocess as sp
from tempfile import NamedTemporaryFile
import os
import sys
import re
import glob


class Mutation:
    def __init__(self, test_cmd: str, spectrum: Spectrum, formula: str,
                 aggr: Callable, compile_cmd: Optional[str] = None,
                 srcdir: str = '**/', method_lvl: bool = False):
        self.spectrum = spectrum
        self.formula = formula
        self.aggr = aggr
        self._mutant_dir = osp.join(osp.curdir, 'mutants')
        os.makedirs(self._mutant_dir, exist_ok=True)
        self._test_cmd = test_cmd
        self._srcdir = srcdir
        self._method_lvl = method_lvl
        self._compile_cmd = compile_cmd
        all_test_cmd = re.sub("\\[.*<<TEST>>.*\\]", "", test_cmd)
        initial_ts = sp.run(all_test_cmd, text=True, shell=True,
                            capture_output=True)
        self._failing_tests = self._parse_mutant(initial_ts.stdout)
        self._mutant_logs = osp.join(osp.curdir, 'mutant_logs')
        os.makedirs(self._mutant_logs, exist_ok=True)

    def filter_ranking(self, ranking: Ranking, cutoff=3):
        """
        Filter the given ranking based on mutation results to push up
        suspicious elements and push down unsuspicious elements according to
        the mutation results. By default, only the top 10 elements will be
        filtered, however this can be altered by setting `cutoff`. Setting
        `cutoff` to -1 will enable filtering of the entire ranking.
        """
        new_ranking = Ranking(1)
        r_iter = iter(ranking)
        group_index = len(self.spectrum.groups())+1
        try:
            for _ in range(cutoff):
                rank = next(r_iter)
                new_groups: Dict[float, Spectrum.Group] = {}
                exe = self.spectrum.p[rank.group] + self.spectrum.f[rank.group]
                for elem in rank.group.get_elements():
                    score = self.mutate_element(elem)
                    if (score not in new_groups):
                        new_groups[score] = Spectrum.Group()
                    new_groups[score].append(elem)
                # Add groups in order of mutation scores
                for score, group in sorted(new_groups.items(), reverse=True,
                                           key=lambda x: x[0]):
                    group.set_index(group_index)
                    group_index += 1
                    new_ranking.append(group, rank.score, exe)
        except StopIteration:
            pass
        try:
            os.rmdir(self._mutant_dir)
        except FileNotFoundError as e:
            errors.warning("Could not remove mutant directory:", e)
        new_ranking.sort(True)
        return new_ranking

    def mutate_element(self, elem: Spectrum.Element) -> float:
        """ Mutate a single element from the spectrum, and return score """
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
        # Build testing command
        if ("<<TEST>>" in self._test_cmd):
            test_cmds = []
            exe_tests = self.spectrum.get_tests(elem)
            for test in exe_tests:
                test_name = test.name.replace("#", "::")
                next_test_cmd = re.sub('\\[(.*)<<TEST>>(.*)\\]',
                                       f'\\1{test_name}\\2', self._test_cmd)
                test_cmds.append(next_test_cmd)
            test_cmd = ';'.join(test_cmds)
        else:
            test_cmd = self._test_cmd
        # Analyze mutants
        try:
            sys.argv = ['analyze_mutants', srcfile, test_cmd,
                        '--verbose', '--mutantDir', self._mutant_dir]
            # Add compile command if available
            if (self._compile_cmd is not None):
                sys.argv.extend(['--numMutants', '100', '--compileCommand',
                                 self._compile_cmd])
            with redirect_stdout(stdout_results := StringIO()):
                analyze.main()
        except SystemExit:
            pass
        stdout_results_str = stdout_results.getvalue()
        # Parse the results
        mut_scores = self._parse_results(stdout_results_str, elem=elem)
        self._clean_up(srcfile)
        score = self.aggr(mut_scores) if len(mut_scores) > 0 else 0.0
        # Store log file
        with NamedTemporaryFile('w', dir=self._mutant_logs,
                                delete=False) as tmp:
            print("Element:", elem, score, file=tmp)
            print(mut_scores, file=tmp)
            print(stdout_results_str, file=tmp)
        return score

    def _parse_results(self, stdout_results_str: str,
                       elem=None) -> List[float]:
        mutants = re.split('=+\n', stdout_results_str)
        mutant_scores = []
        for mutant in mutants:
            # first check if mutant was terminated
            if ("HAD TO TERMINATE ANALYSIS" in mutant):
                # remove this mutant from evaluation
                continue
            try:
                failing_tests = self._parse_mutant(mutant)
                if (elem is not None):
                    exe_tests = self.spectrum.get_tests(elem)
                    orig_failing = self._failing_tests.intersection(exe_tests)
                else:
                    orig_failing = self._failing_tests
                fail_pass = len(orig_failing.difference(failing_tests))
                pass_fail = len(failing_tests.difference(orig_failing))
                sus = Suspicious(fail_pass, self.spectrum.tf, pass_fail,
                                 self.spectrum.tp)
                score = sus.execute('muse')
                mutant_scores.append(score)
            except StopIteration:
                continue
        return mutant_scores

    def _parse_mutant(self, mutant: str) -> Set[Spectrum.Test]:
        mutant_lines = mutant.splitlines()
        start = next(i for i in range(len(mutant_lines))
                     if mutant_lines[i].startswith("Failing tests"))+1
        failing_tests = set()
        while (start > 0):
            i = 0
            while (start+i < len(mutant_lines) and
                   (m := re.match('\\s*-\\s+(.+)', mutant_lines[start+i]))):
                tests = self.spectrum.search_tests(m.group(1).replace('::', '#'))
                if (len(tests) == 0):
                    raise ValueError(f'Could not find unique test "{m.group(1)}"')
                failing_tests.add(sorted(tests, key=lambda x: len(str(x)))[0])
                i += 1
            start = next((i for i in range(start, len(mutant_lines))
                        if mutant_lines[i].startswith("Failing tests")), -2)+1
        return failing_tests

    def _clean_up(self, srcfile):
        for file in glob.glob(osp.join(self._mutant_dir, "*")):
            os.remove(file)
        for umbackup in glob.glob(srcfile+'*um.backup*'):
            os.remove(umbackup)
