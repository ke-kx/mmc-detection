from collections import defaultdict
import logging

# todo if ae too slow:
# idea: already build call vectors (1 if call present) when generating tus
# then it's as simple as subtracting the vectors and checking the abs (right?)
# well, actually counting the +1 and -1s and from there havving the difs i think

from .score import Score


class AEScore(Score):
    def __init__(self):
        self.e = 0
        self.ae = 0
        self.missing_call_count = defaultdict(int)
        self.mcstrings = None

    def score(self):
        return 1.0 - (self.e / (self.e + self.ae))

    def predictions(self):
        total_calls = sum(self.missing_call_count.values())
        return [(prediction, call_count / total_calls) for prediction, call_count in self.missing_call_count.items()]

    def setmcstrings(self, db):
        self.mcstrings = {}
        for prediction, confidence in self.predictions():
            calls = [db.getmethod(methodId) for methodId in prediction]
            self.mcstrings[calls.__repr__()] = confidence

    def __str__(self):
        missingcalls = self.mcstrings if self.mcstrings else self.missing_call_count
        return "Score: {0} (E: {1}, AE: {2}, missing: {3}"\
            .format(self.score(), self.e, self.ae, missingcalls)


class AlmostEqualDetector(object):
    def __init__(self, n=1, anomaly_threshold=0.9):
        self.n = n
        self.anomaly_threshold = anomaly_threshold

    def analyze(self, typeusages):
        """Go through all given TUs and check how anomalous they are.
        Return a dict with id to Score object mapping
        """
        scores = defaultdict(AEScore)
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
                    score.missing_call_count[missing] += 1
                elif self._almost_equal(tu_b, tu_a):
                    score = scores[tu_b.id]
                    score.ae += 1

                    missing = frozenset(tu_a.calls - tu_b.calls)
                    score.missing_call_count[missing] += 1

        # calculate confidence of predictions
        return scores

    def is_anomalous(self, score):
        """Return true if the given score makes a typeusage anomalous"""
        return score.score() > self.anomaly_threshold

    @staticmethod
    def _equal(tu_a, tu_b):
        return tu_a.calls == tu_b.calls

    def _almost_equal(self, tu_a, tu_b):
        if len(tu_a.calls) + self.n != len(tu_b.calls):
            return False

        return tu_a.calls.issubset(tu_b.calls)

    def __hash__(self):
        return hash((self.__class__, self.n, self.anomaly_threshold))

    def __eq__(self, other):
        return (self.n, self.anomaly_threshold) == (other.n, other.anomaly_threshold)

    def __repr__(self):
        return "AlmostEqualDetector (n={0})".format(self.n)

    def __str__(self):
        return "AlmostEqualDetector with n={0}".format(self.n)
