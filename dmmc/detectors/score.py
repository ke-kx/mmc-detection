class Score(object):
    def score(self):
        NotImplementedError("Should override this method!")

    def __repr__(self):
        return "Score: {0}".format(self.score())
