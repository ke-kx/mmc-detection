from collections import defaultdict

# todo if ae too slow:
# idea: already build call vectors (1 if call present) when generating tus
# then it's as simple as subtracting the vectors and checking the abs (right?)
# well, actually counting the +1 and -1s and from there havving the difs i think


class Score(object):
    def __init__(self):
        self.e = 0
        self.ae = 0
        self.missingcalls = defaultdict(int)
        self.mcstrings = None

    def score(self):
        return 1.0 - (self.e / (self.e + self.ae))

    def setmcstrings(self, db):
        self.mcstrings = {}
        for set in self.missingcalls.keys():
            calls = [db.getmethod(methodId) for methodId in set]
            self.mcstrings[calls.__repr__()] = self.missingcalls[set]

    def __str__(self):
        missingcalls = self.mcstrings if self.mcstrings else self.missingcalls
        return "Score: {0} (E: {1}, AE: {2}, missing: {3}"\
            .format(self.score(), self.e, self.ae, missingcalls)

    def __repr__(self):
        return "Score: {0}".format(self.score())


class AlmostEqualDetector(object):
    def __init__(self, n):
        self.n = n

    def analyze(self, typeusages):
        """Go through all given TUs and check how anomalous they are.
        Return a dict with id to Score object mapping
        """
        scores = defaultdict(Score)
        typeusages = list(typeusages)

        for idx, tu_a in enumerate(typeusages):
            for tu_b in typeusages[idx:]:
                if self._equal(tu_a, tu_b):
                    scores[tu_a.id].e += 1
                    scores[tu_b.id].e += 1
                    if tu_a == tu_b: scores[tu_a.id].e -= 1  # compensate for when comparing with itself
                elif self._almost_equal(tu_a, tu_b):
                    score = scores[tu_a.id]
                    score.ae += 1

                    missing = frozenset(tu_b.calls - tu_a.calls)
                    score.missingcalls[missing] += 1
                elif self._almost_equal(tu_b, tu_a):
                    score = scores[tu_b.id]
                    score.ae += 1

                    missing = frozenset(tu_a.calls - tu_b.calls)
                    score.missingcalls[missing] += 1

        return scores

    @staticmethod
    def _equal(tu_a, tu_b):
        return tu_a.calls == tu_b.calls

    def _almost_equal(self, tu_a, tu_b):
        if len(tu_a.calls) + self.n != len(tu_b.calls):
            return False

        return tu_a.calls.issubset(tu_b.calls)
