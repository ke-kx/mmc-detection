
from sklearn.neighbors import LocalOutlierFactor
import numpy as np

from .score import Score


class LOFScore(Score):
    def __init__(self, value):
        self.value = value

    def score(self):
        # value is already negative, thus this brings
        # TODO this doesn't work, need to determine max score + normalize into [0, 1](?)
        # TODO additionally right now there seem to be a ton of outliers?!
        return 1 + self.value


# http://scikit-learn.org/stable/modules/generated/sklearn.neighbors.LocalOutlierFactor.html#sklearn.neighbors.LocalOutlierFactor
class LocalOutlierFactorDetector(object):
    def __init__(self, n_neighbors=10):
        self.n_neighbors = n_neighbors
        # TODO experiment with additional parameters
        self.lof = LocalOutlierFactor(n_neighbors)

    def analyze(self, typeusages):
        # number of samples too small to run analysis
        if len(typeusages) < self.n_neighbors:
            return {tu.id: LOFScore(0) for tu in typeusages}

        data = np.array([tu.vector() for tu in typeusages])
        results = self.lof.fit_predict(data)

        print(results)
        print(self.lof.negative_outlier_factor_)

        scores = {tu.id: LOFScore(res) for tu, res in zip(typeusages, self.lof.negative_outlier_factor_)}
        return scores


if __name__ == "__main__":

    import argparse
    import logging

    from ..database import Connector, ContextTypeLoader, TypeLoader
    from ..dmmc import Runner

    parser = argparse.ArgumentParser(description="Test database connectivity")
    parser.add_argument('database', help='Name of database to connect to')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    logging.info("LOF TestRun on database %s", args.database)

    loader = ContextTypeLoader(args.database)
    # loader = TypeLoader(args.database)
    detectors = [LocalOutlierFactorDetector()]
    runner = Runner(loader, detectors)

    results = runner.run()

    print(results)

    print("")
    logging.warning("Sorting results!")
    results_sorted = sorted(results, key=lambda x: x[1].score(), reverse=True)
    print(results_sorted[:50])

    print("")
    logging.warning("First 10 ids")
    db = Connector(args.database)
    for id, score in results_sorted[:100]:
        tu = db.gettypeusage(id)
        print(score, tu)
