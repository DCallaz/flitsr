import copy
from typing import List, Set, TYPE_CHECKING
if TYPE_CHECKING:
    from flitsr.args import Args
from flitsr.spectrum import Spectrum
from flitsr.errors import warning
from flitsr.ranking import Ranking, Tiebrk, set_orig, unset_orig
from flitsr.advanced.ranker import Ranker
from flitsr.advanced.sbfl import SBFL
from flitsr.advanced.attributes import existing, choices, print_name
from flitsr import advanced


class Flitsr(Ranker):
    """
    Run the main FLITSR algorithm over the spectrum to produce ranked lists.
    """
    @existing('tiebrk')
    @existing('args')
    @choices('internal_ranking', ['auto', 'conf', 'original', 'reverse',
                                  'flitsr'])
    def __init__(self, args: 'Args', internal_ranking: str = 'auto',
                 tiebrk: Tiebrk = Tiebrk.ORIG):
        self.tiebrk = tiebrk
        self.args = args
        self.order_method = internal_ranking

    def remove_faulty_elements(self, spectrum: Spectrum,
                               tests_removed: Set[Spectrum.Test],
                               faulty: List[Spectrum.Group]):
        """Removes all tests that execute an 'actually' faulty element"""
        toRemove = []
        for test in tests_removed:
            for f in faulty:
                if (spectrum[test][f] is True):
                    toRemove.append(test)
                    break
        tests_removed.difference_update(toRemove)

    def run_metric(self, spectrum: Spectrum, formula: str):
        if (hasattr(advanced.RankerType, formula.upper())):
            ranker_args = self.args.get_arg_group(formula)
            ranker = advanced.RankerType[formula.upper()].value(**ranker_args)
            ranking = ranker.rank(spectrum, formula)
        else:
            sbfl_args = self.args.get_arg_group('SBFL')
            ranking = SBFL(**sbfl_args).rank(spectrum, formula)
        return ranking

    def flitsr(self, spectrum: Spectrum, formula: str) -> List[Spectrum.Group]:
        """
        Executes the recursive flitsr algorithm to identify faulty elements
        """
        if (spectrum.tf == 0):
            return []
        ranking = self.run_metric(spectrum, formula)
        r_iter = iter(ranking)
        entity = next(r_iter).entity
        tests_removed = spectrum.get_tests(entity, only_failing=True,
                                           remove=True, bucket='flitsr')
        while (len(tests_removed) == 0):  # sanity check
            if ((s2 := next(r_iter, None)) is None):
                count_non_removed = len(spectrum.failing())
                warning("flitsr found", count_non_removed,
                        "failing test(s) that it could not explain")
                return []
            # continue trying the next element if available
            entity = s2.entity
            tests_removed = spectrum.get_tests(entity, only_failing=True,
                                               remove=True, bucket='flitsr')
        faulty = self.flitsr(spectrum, formula)
        self.remove_faulty_elements(spectrum, tests_removed, faulty)
        if (len(tests_removed) > 0):
            faulty.append(entity)
        return faulty

    def get_inverse_confidence_scores(self, spectrum: Spectrum,
                                      basis: List[Spectrum.Group]) -> List[int]:
        """
        Using the given basis and spectrum, calculates the confidence scores
        for each basis element. The confidence scores returned are the inverse
        of the actual confidence scores.
        """
        confs: List[int] = []
        for entity in basis:
            ts = list(spectrum.get_tests(entity, only_failing=True))
            possibles: Set[Spectrum.Group] = set()
            possibles.update(spectrum.get_executed_groups(ts[0]))
            for test in ts[1:]:
                possibles.intersection_update(spectrum.get_executed_groups(test))
            confs.append(len(possibles))
        return confs

    def flitsr_ordering(self, spectrum: Spectrum, basis: List[Spectrum.Group],
                        ranking: Ranking,
                        flitsr_order='auto') -> List[Spectrum.Group]:
        """
        Order the given flitsr basis using the specified ordering strategy.
        Strategies include 'auto', 'conf', 'original', 'reverse', and 'flitsr'.
        'flitsr' preserves the current ordering of the basis, 'reverse'
        reverses this order (i.e. order elements were identified by flitsr),
        'original' orders elements by their position in the original ranking
        (given by ranking). 'conf' gets the confidence scores for each element
        and orders by these. 'auto' also gets the confidence scores for each
        element and uses them to pick which strategy to use (either 'flitsr',
        'original' or 'conf').
        """
        if (len(basis) == 0):
            return basis
        inv_confs = []
        # check if internal ranking order needs to be determined
        if (flitsr_order in ['auto', 'conf']):
            inv_confs = self.get_inverse_confidence_scores(spectrum, basis)
        if (flitsr_order == 'auto'):
            if (all(c > 3 for c in inv_confs)):
                flitsr_order = 'original'
            elif (all(c <= 3 for c in inv_confs)):
                flitsr_order = 'flitsr'
            else:
                flitsr_order = 'conf'
            # check for big groups
            big, small = [], []
            for entity in basis:
                if (len(entity) > 5):
                    big.append(entity)
                else:
                    small.append(entity)
            if (len(big) != 0 and len(small) != 0):
                return self.flitsr_ordering(spectrum, small, ranking,
                                            flitsr_order) + \
                    self.flitsr_ordering(spectrum, big, ranking, flitsr_order)
        # reorder basis
        if (flitsr_order == 'flitsr'):
            ordered_basis = basis
        elif (flitsr_order == 'reverse'):
            ordered_basis = list(reversed(basis))
        elif (flitsr_order == 'original'):
            ordered_basis = [x.entity for x in ranking if x.entity in basis]
            # add any missing elements
            if (len(ordered_basis) < len(basis)):
                ordered_basis.extend([e for e in basis if e not in ordered_basis])
        elif (flitsr_order == 'conf'):
            ordered_basis = [x for _, x in sorted(zip(inv_confs, basis),
                                                  key=lambda x: x[0])]
        return ordered_basis

    def rank(self, spectrum: Spectrum, formula: str) -> Ranking:
        ranking = self.run_metric(spectrum, formula)
        set_orig(ranking)
        val = 2**64
        basis = self.flitsr(spectrum, formula)
        spectrum.reset(bucket='flitsr')
        if (not basis == []):
            ordered_basis = self.flitsr_ordering(spectrum, basis, ranking,
                                                 self.order_method)
            for x in ranking:
                if (x.entity in basis):
                    x.score = val - ordered_basis.index(x.entity)
            val = val-len(basis)
        # Reset the coverage matrix and counts
        ranking.sort(True)
        unset_orig()
        return ranking


@print_name('flitsr_multi')
class Multi(Flitsr):
    """
    Run the FLITSR* algorithm over the spectrum to produce ranked lists.
    """
    @existing('args')
    def __init__(self, args: 'Args'):
        flitsr_opts = args.get_arg_group('FLITSR')
        super().__init__(**flitsr_opts)

    def multiRemove(self, spectrum: Spectrum,
                    faulty: List[Spectrum.Group]) -> bool:
        """
        Remove the elements given by faulty from the spectrum, and remove any
        test cases executing these elements only.
        """
        # Get tests executing elems in faulty set
        executing: Set[Spectrum.Test] = set()
        for elem in faulty:
            exe = spectrum.get_tests(elem, only_failing=True)
            executing.update(exe)

        # Remove all elements in faulty set
        for group in faulty:
            spectrum.remove_group(group, bucket='multi')

        multiFault = False
        for test in executing:
            for group in spectrum.groups():  # remaining groups not in faulty
                if (spectrum[test][group]):
                    break
            else:
                multiFault = True
                spectrum.remove_test(test, bucket='multi')
        return multiFault

    def rank(self, spectrum: Spectrum, formula: str) -> Ranking:
        ranking = self.run_metric(spectrum, formula)
        set_orig(ranking)
        val = 2**64
        newSpectrum = copy.deepcopy(spectrum)
        while (newSpectrum.tf > 0):
            basis = self.flitsr(newSpectrum, formula)
            if (not basis == []):
                ordered_basis = self.flitsr_ordering(spectrum, basis, ranking,
                                                     self.order_method)
                for x in ranking:
                    if (x.entity in basis):
                        x.score = val - ordered_basis.index(x.entity)
                val = val-len(basis)
            else:  # (fall-back) finish FLITSR* if basis is empty
                break
            # Reset the coverage matrix and counts
            newSpectrum.reset(bucket='flitsr')
            # Next iteration can be either multi-fault, or multi-explanation
            # multi-fault -> we assume multiple faults exist
            # multi-explanation -> we assume there are multiple explanations
            # for the same faults
            self.multiRemove(newSpectrum, basis)
            val = val-1
        ranking.sort(True)
        unset_orig()
        return ranking
