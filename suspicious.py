import math

class Suspicious() :
    """
    An implementation of ranking metric used for
    fault localization
    """
    def __init__(self, ef, tf, ep, tp) :
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

    def tarantula(self) :
        """
        Ref: Jones, J. A., and Harrold, M. J.Empirical evaluation
        of the Tarantula automatic fault-localization technique.
        In 20th IEEE/ACM International Conference on
        Automated Software Engineering (ASE 2005),
        November 7-11, 2005, Long Beach,CA, USA(2005),
        D. F. Redmiles, T. Ellman, and A. Zisman, Eds., ACM, pp. 273–282
        """
        if self.ef == 0 :
            return  0.0
        nominator = self.ef / self.tf
        passed_component = self.ep
        if (self.ep):
            passed_component /= self.tp
        denominator = nominator + passed_component
        score = nominator / denominator
        return round(score, 4)

    def ochai(self) :
        """
        Ref: Ochiai, A. Zoogeographical studies on the soleoid
        fishes found in japan and its neighhouring regions-ii.
        Bulletin of the Japanese Society of Scientific Fisheries
        22, 9 (1957), 526–530
        """
        if self.ef == 0 :
            return 0.0
        e = (self.ef + self.ep) * self.tf
        denominator = math.sqrt(e)
        score = self.ef / denominator
        return round(score, 4)

    def jaccard(self) :
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
        score = self.ef / denominator
        return round(score, 4)

    def dstar(self) :
        """
        Ref: Wong, W. E., Debroy, V., Gao, R., and Li, Y.
        The dstar method for effective software fault localization.
        IEEE Trans. Reliability 63, 1 (2014), 290–308
        """
        if self.ef == 0 :
            return 0.0
        nominator = self.ef * self.ef
        denominator = self.nf + self.ep
        if denominator == 0:
            return math.inf
        score = nominator / denominator
        return round(score, 4)

    def gp13(self) :
        """
        Yoo, S. Evolving human competitive spectra-based fault localisation
        techniques. In: Proceedings of the 4th International Conference onSearch
        Based Software Engineering, (2012).
        """
        if self.ef == 0 :
            return 0.0
        denominator = self.ef + 2*self.ep
        if denominator == 0:
            return math.inf
        score = self.ef * (1 + 1/denominator)
        return round(score, 4)

    def wong2(self) :
        """
        ???
        """
        score = self.ef - self.ep
        return round(score, 4)

    def naish2(self):
        """
        Ref: Naish, L., Lee, H. J., Ramamohanarao, K. A model for spectra-based software
        diagnosis. ACM Trans. Softw. Eng. Methodol. (2011), 20(3):1-32
        """
        nominator = self.ep
        denominator = self.np + self.ep + 1
        if denominator == 0:
            return math.inf
        score = self.ef - (nominator/denominator)
        return round(score, 4)

    def overlap(self):
        """
        ???
        """
        if self.ef == 0 :
            return 0.0
        denominator = min(self.ef, self.nf, self.ep)
        if denominator == 0:
            return math.inf
        score = self.ef / denominator
        return round(score, 4)

    def harmonic(self):
        """
        ???
        """
        n1 = (self.ef*self.np-self.nf*self.ep)
        n2 = ((self.ef+self.ep)*(self.np+self.nf)+(self.ef+self.nf)*(self.ep+self.np))
        nominator = n1*n2
        denominator = (self.ef+self.ep)*(self.np+self.nf)*(self.ef+self.nf)*(self.ep+self.np)+1
        if denominator == 0:
            return math.inf
        score = nominator / denominator
        return round(score, 4)
