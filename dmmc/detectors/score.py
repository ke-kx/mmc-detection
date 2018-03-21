from collections import defaultdict


class Score(object):
    def predictions(self):
        """Return list of tuples containg predictions and their confidence"""
        NotImplementedError("Should override this method!")

    def score(self):
        NotImplementedError("Should override this method!")

    def __repr__(self):
        return "Score: {0}".format(self.score())
