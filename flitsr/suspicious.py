import math
from typing import List
from flitsr.spectrum import Spectrum
from flitsr.score import Scores


class Suspicious():
    """
    An implementation of ranking metric used for
    fault localization
    """
    def __init__(self, ef: int, tf: int, ep: int, tp: int):
        """
        The four basic counts that are parameters to
        different metrics
        :param ef : no. of failed tests that use e
        :param tf : total failed tests
        :param ep : no. of passed tests that use e
        :param tp : total passed tests
        """
        self.ef = ef
        self.tf = tf
        self.ep = ep
        self.tp = tp
        self.nf = tf - ef
        self.np = tp - ep

    def execute(self, metric: str) -> float:
        func = getattr(self, metric)
        return func()

    @staticmethod
    def apply_formula(spec: Spectrum, formula: str,
                      tiebrk: int, reverse=True) -> Scores:
        """
        Calculate the scores for each of the elements using the given formula.
        Assumes a non-empty spectrum.
        """
        scores: Scores = Scores()
        for elem in spec.elements:
            sus = Suspicious(spec.f[elem], spec.tf, spec.p[elem], spec.tp)
            exect = spec.p[elem]+spec.f[elem]
            scores.append(elem, sus.execute(formula), exect)
        scores.sort(reverse, tiebrk)
        return scores

    @staticmethod
    def getNames() -> List[str]:
        all_names = dir(Suspicious)
        names = [x for x in all_names if (not x.startswith("_")
                 and x != "execute" and x != "getNames"
                 and x != "apply_formula")]
        return names

    def _ample(self) -> float:
        t1 = 0.0 if (self.ef == 0) else self.ef/self.tf
        t2 = 0.0 if (self.ep == 0) else self.ep/self.tp
        return abs(t1 - t2)

    def _anderberg(self) -> float:
        if (self.ef == 0):
            return 0.0
        denominator = (self.ef + 2*(self.nf + self.ep))
        return self.ef/denominator

    def _arith_mean(self) -> float:
        denominator = (self.ef + self.ep)*(self.np + self.nf) + self.tf*self.tp
        nominator = 2*self.ef*self.np - 2*self.nf*self.ep
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _cohen(self) -> float:
        denominator = (self.ef + self.ep)*self.tp + self.tf*(self.nf + self.np)
        nominator = 2*self.ef*self.np - 2*self.nf*self.ep
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _dice(self) -> float:
        if (self.ef == 0):
            return 0.0
        denominator = self.tf + self.ep
        return 2*self.ef/denominator

    def _euclid(self) -> float:
        return math.sqrt(self.ef + self.np)

    def _fleiss(self) -> float:
        denominator = (2*self.ef*self.nf*self.ep) + (2*self.np*self.nf*self.ep)
        nominator = (4*self.ef*self.np) - (4*self.nf*self.ep) - (self.nf - self.ep)**2
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _geometric(self) -> float:
        denominator = math.sqrt((self.ef + self.ep)*(self.np + self.nf)*self.tf*self.tp)
        nominator = self.ef*self.np - self.nf*self.ep
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _goodman(self) -> float:
        denominator = 2*self.ef + self.nf + self.ep
        nominator = 2*self.ef - self.nf - self.ep
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _hamann(self) -> float:
        denominator = self.tf + self.tp
        nominator = self.ef + self.np  - self.nf - self.ep
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _hamming(self) -> float:
        return self.ef + self.np

    def harmonic(self) -> float:
        n1 = (self.ef*self.np - self.nf*self.ep)
        n2 = ((self.ef + self.ep)*(self.np + self.nf) + self.tf*self.tp)
        nominator = n1*n2
        denominator = (self.ef + self.ep)*(self.np + self.nf)*self.tf*self.tp
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def jaccard(self) -> float:
        """
        Ref: Chen, M. Y., Kiciman, E., Fratkin, E., Fox, A., and Brewer, E. A.
        Pinpoint: Problem determination in large, dynamicinternet services.
        In 2002 International Conference on Dependable Systems
        and Networks (DSN 2002), 23-26 June 2002,
        Bethesda, MD, USA, Proceedings(2002), IEEE Computer Society,
        pp. 595–604
        """
        if self.ef == 0 :
            return 0.0
        denominator = self.tf + self.ep
        return self.ef/denominator

    def _kulczynski1(self) -> float:
        denominator = self.nf + self.ep
        if (self.ef == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return self.ef/denominator

    def _kulczynski2(self) -> float:
        t1 = 0.0 if (self.ef == 0) else self.ef/self.tf
        t2 = 0.0 if (self.ef == 0) else self.ef/(self.ef + self.ep)
        return 0.5*(t1 + t2)

    def _m1(self) -> float:
        denominator = self.nf + self.ep
        nominator = self.ef + self.np
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _m2(self) -> float:
        if (self.ef == 0):
            return 0.0
        denominator = self.ef + self.np + 2*(self.ef + self.ep)
        return self.ef/denominator

    def ochiai(self) -> float:
        """
        Ref: Ochiai, A. Zoogeographical studies on the soleoid
        fishes found in japan and its neighhouring regions-ii.
        Bulletin of the Japanese Society of Scientific Fisheries
        22, 9 (1957), 526–530
        """
        denominator = math.sqrt(self.tf * (self.ef + self.ep))
        if (self.ef == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return self.ef/denominator

    def _ochiai2(self) -> float:
        nominator = self.ef*self.np
        denominator = math.sqrt((self.ef + self.ep)*(self.np + self.nf)*self.tf*self.tp)
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def overlap(self) -> float:
        denominator = min(self.ef, self.nf, self.ep)
        if (self.ef == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return self.ef/denominator

    def _rogers_tanimoto(self) -> float:
        nominator = self.ef + self.np
        denominator = self.ef + self.np + 2*(self.nf + self.ep)
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _rogot1(self) -> float:
        t1 = 0.0 if (self.ef == 0) else self.ef/(2*self.ef + self.nf + self.ep)
        t2 = 0.0 if (self.np == 0) else self.np/(2*self.np + self.nf + self.ep)
        return 0.5*(t1 + t2)

    def _rogot2(self) -> float:
        t1 = 0.0 if (self.ef == 0) else self.ef/(self.ef + self.ep)
        t2 = 0.0 if (self.ef == 0) else self.ef/self.tf
        t3 = 0.0 if (self.np == 0) else self.np/self.tp
        t4 = 0.0 if (self.np == 0) else self.np/(self.np + self.nf)
        return 0.25*(t1 + t2 + t3 + t4)

    def _russell_rao(self) -> float:
        if (self.ef == 0):
            return 0.0
        denominator = self.tf + self.tp
        return self.ef/denominator

    def _scott(self) -> float:
        nominator = 4*self.ef*self.np - 4*self.nf*self.ep - (self.nf - self.ep)**2
        denominator = (2*self.ef + self.nf + self.ep)*(2*self.np + self.nf + self.ep)
        if (nominator == 0):
            return 0.0
        elif (denominator == 0):
            return math.inf
        return nominator/denominator

    def _simpl_match(self) -> float:
        nominator = self.ef + self.np
        if (nominator == 0):
            return 0.0
        denominator = self.tf + self.tp
        return nominator/denominator

    def _sokal(self) -> float:
        nominator = 2*(self.ef + self.np)
        denominator = nominator + self.nf + self.ep
        if (nominator == 0):
            return 0.0
        return nominator/denominator

    def _sorensen_dice(self) -> float:
        nominator = 2*self.ef
        if (nominator == 0):
            return 0.0
        denominator = nominator + self.nf + self.ep
        return nominator/denominator

    def tarantula(self) -> float:
        """
        Ref: Jones, J. A., and Harrold, M. J.Empirical evaluation
        of the Tarantula automatic fault-localization technique.
        In 20th IEEE/ACM International Conference on
        Automated Software Engineering (ASE 2005),
        November 7-11, 2005, Long Beach,CA, USA(2005),
        D. F. Redmiles, T. Ellman, and A. Zisman, Eds., ACM, pp. 273–282
        """
        if (self.ef == 0):
            return  0.0
        nominator = self.ef / self.tf
        passed_component = 0.0 if (self.ep == 0) else self.ep/self.tp
        denominator = nominator + passed_component
        return nominator/denominator

    def _wong1(self) -> float:
        return self.ef

    def _wong2(self) -> float:
        return self.ef - self.ep

    def _wong3(self) -> float:
        if (self.ep <= 2):
            return self.ef - self.ep
        elif (self.ep <= 10):
            return self.ef - (2 + 0.1*(self.ep - 2))
        else:
            return self.ef - (2.8 + 0.001*(self.ep - 10))

    def zoltar(self) -> float:
        if self.ef == 0 :
            return  0.0
        multifault_component = 10000*(self.nf*self.ep)/self.ef
        denominator =  self.tf + self.ep + multifault_component
        return self.ef / denominator

    def naish2(self) -> float:
        """
        Ref: Naish, L., Lee, H. J., Ramamohanarao, K. A model for spectra-based software
        diagnosis. ACM Trans. Softw. Eng. Methodol. (2011), 20(3):1-32
        """
        return self.ef - (self.ep/(self.tp+1))

    def dstar(self, p=2) -> float:
        """
        Ref: Wong, W. E., Debroy, V., Gao, R., and Li, Y.
        The dstar method for effective software fault localization.
        IEEE Trans. Reliability 63, 1 (2014), 290–308
        """
        nominator = self.ef**p
        denominator = self.ep + self.nf
        if (nominator == 0):
            return 0.0
        elif denominator == 0:
            return math.inf
        return nominator/denominator

    def gp13(self) -> float:
        """
        Yoo, S. Evolving human competitive spectra-based fault localisation
        techniques. In: Proceedings of the 4th International Conference onSearch
        Based Software Engineering, (2012).
        """
        if (self.ef == 0):
            return 0.0
        denominator = 2*self.ep + self.ef
        return self.ef*(1 + 1/denominator)

    def hyperbolic(self) -> float:
        if (self.ef + self.ep == 0 or self.tf == 0):
            return 0.0
        K1 = 0.375
        K2 = 0.768
        K3 = 0.711
        t1 = 1/(K1 + (self.nf/self.tf))
        t2 = K3/(K2 + self.ep/(self.ef + self.ep))
        return t1 + t2

    def _old_barinel(self) -> float:
        if (self.nf == 0 or self.ep + self.ef == 0):
            return 0.0
        if (self.ep == 0):
            h = 0.0
        else:
            h = self.ep/(self.ep + self.ef)
        return h**(self.ep) * (1-h)**(self.ef)

    def barinel(self) -> float:
        if (self.nf == 0 or self.ep + self.ef == 0):
            return 0.0
        if (self.ep == 0):
            h = 0.0
        else:
            h = self.ep/(self.ep + self.ef)
        return h**(self.ep) * (1-h)**(11)
