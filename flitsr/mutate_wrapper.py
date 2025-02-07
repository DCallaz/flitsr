from flitsr.universalmutator import genmutants, analyze
from flitsr.spectrum import Spectrum
from flitsr import errors
from flitsr.ranking import Ranking
from typing import List, Tuple, Set, Dict, Optional
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
    def __init__(self, test_cmd: str, spectrum: Spectrum,
                 compile_cmd: Optional[str] = None, srcdir: str = '**/',
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
        self._mutant_logs = osp.join(osp.curdir, 'mutant_logs')
        os.makedirs(self._mutant_logs, exist_ok=True)

    def filter_ranking(self, ranking: Ranking, cutoff=5):
        """
        Filter the given ranking based on mutation results to push up
        suspicious elements and push down unsuspicious elements according to
        the mutation results. By default, only the top 10 elements will be
        filtered, however this can be altered by setting `cutoff`. Setting
        `cutoff` to -1 will enable filtering of the entire ranking.
        """
        new_ranking = Ranking(ranking._tiebrk)
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
                for score, group in new_groups.items():
                    group.set_index(group_index)
                    group_index += 1
                    new_ranking.append(group, rank.score+score, exe)
            os.rmdir(self._mutant_dir)
        except StopIteration:
            pass
        except FileNotFoundError:
            errors.warning("Could not remove mutant directory")
        return ranking

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
                next_test_cmd = self._test_cmd.replace("<<TEST>>", test_name)
                test_cmds.append(next_test_cmd)
            test_cmd = ';'.join(test_cmds)
        else:
            test_cmd = self._test_cmd
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
        stdout_results_str = stdout_results.getvalue()
        with NamedTemporaryFile('w', dir=self._mutant_logs,
                                delete=False) as tmp:
            print("Element:", elem, file=tmp)
            print(stdout_results_str, file=tmp)
        # Parse the results
        fpm, pfm, nm = self._parse_results(stdout_results_str)
        self._clean_up(srcfile)
        return (0 if nm == 0 else fpm/nm if fpm > 0 else -pfm/nm)

    def _parse_results(self, stdout_results_str: str) -> Tuple[int, int, int]:
        mutants = re.split('=+\n', stdout_results_str)
        num_mutants = 0
        fail_pass_mutants = 0  # num mutants where at least one failing -> pass
        pass_fail_mutants = 0  # num mutants where at least one pass -> failing
        for mutant in mutants:
            try:
                failing_tests = self._parse_mutant(mutant)
                fail_pass = len(self._failing_tests.difference(failing_tests))
                pass_fail = len(failing_tests.difference(self._failing_tests))
                if (fail_pass > 0):
                    fail_pass_mutants += 1
                if (pass_fail > 0):
                    pass_fail_mutants += 1
                num_mutants += 1
            except StopIteration:
                continue
        return fail_pass_mutants, pass_fail_mutants, num_mutants

    def _parse_mutant(self, mutant: str) -> Set[Spectrum.Test]:
        mutant_lines = mutant.splitlines()
        start = next(i for i in range(len(mutant_lines))
                     if mutant_lines[i].startswith("Failing tests"))+1
        i = 0
        failing_tests = set()
        while (start > 0):
            while (start+i < len(mutant_lines) and
                   (m := re.match('\\s*-\\s+(.+)', mutant_lines[start+i]))):
                tests = self.spectrum.search_tests(m.group(1).replace('::', '#'))
                if (len(tests) == 0):
                    raise ValueError(f'Could not find unique test "{m.group(1)}"')
                failing_tests.add(sorted(tests, key=lambda x: len(str(x)))[0])
                i += 1
            start = next((i for i in range(len(mutant_lines))
                        if mutant_lines[i].startswith("Failing tests")), -2)+1
        return failing_tests

    def _clean_up(self, srcfile):
        for file in glob.glob(osp.join(self._mutant_dir, "*")):
            os.remove(file)
        for umbackup in glob.glob(srcfile+'*um.backup*'):
            os.remove(umbackup)
