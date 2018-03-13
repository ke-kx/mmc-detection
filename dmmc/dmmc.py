
import logging
from collections import defaultdict
from statistics import mean, median


class Runner(object):
    """Handles the execution of one run with given loader and detectors.
    Saves statistical data and outputs results in a large accumulated list.
    """
    type_filter_list = ['eu.cqse.check.framework.scanner.ETokenType', 'java.lang.StringBuilder']

    def __init__(self, loader, detectors):
        self.loader = loader
        self.detectors = detectors

        self.statisticalData = defaultdict(list)

    def run(self):
        """Main method to start the analysis."""
        results_accumulated = []

        total = self.loader.typeusagecount()

        # go through all separators
        for separator in self.loader.separators():
            logging.info("Analyzing %s", separator)
            if separator.typename in self.type_filter_list: continue

            # obtain all tus for this abstraction level
            typeusages = list(self.loader.data(separator))
            results_accumulated += self.analyze(typeusages)
            logging.info("%d/%d", len(results_accumulated), total)

        return results_accumulated

    def analyze(self, typeusages):
        """Use all given detectors to analyze the typeusages."""
        results_acc = []

        # note relevant data (dataset size, ....)
        # todo do not save in global object
        self.extract_statistical_data(typeusages)

        # throw all anomaly detectors on the given data
        for detector in self.detectors:
            # todo time analysis and save together with statistical data? in meta db
            results = detector.analyze(typeusages)

            # todo write out results to db - here could be smart cause of memory constraints?, but elsewhere would be cleaner
            # todo consider if Database is actually necessary / useful or if text output can be enough
            # todo use separate results database
            # todo this is not going to work right now with multiple detectors...
            results_acc += results.items()

        return results_acc

    def analyze_one(self, tu):
        """"Analyze the given typeusage with all given detectors.
        Ensures that the tu to be analyzed isn't contained twice in the dataset to be analyzed."""
        typeusages = list(self.loader.data(tu.separator()))
        if tu not in typeusages:
            typeusages.append(tu)
        return self.analyze(typeusages)

    def extract_statistical_data(self, typeusages):
        if len(typeusages) > 10:
            self.statisticalData['tuCount'].append(len(typeusages))
            callcount = list(map(lambda tu: len(tu.calls), typeusages))
            self.statisticalData['calllistMin'].append(min(callcount))
            self.statisticalData['calllistMax'].append(max(callcount))
            self.statisticalData['calllistAvg'].append(mean(callcount))
            self.statisticalData['calllistMedian'].append(median(callcount))


def pretty_print_results(dbname, results_sorted, count):
    print("")
    logging.warning("First %d ids", count)
    db = Connector(dbname)
    for id, score in results_sorted[:count]:
        tu = db.gettypeusage(id)
        score.setmcstrings(db)
        print(score, tu)
        # print(tu.type)
        # print(tu.vector())


if __name__ == '__main__':

    import argparse

    from .database import Connector, ContextTypeLoader, TypeLoader
    from .detectors.almostequal import AlmostEqualDetector

    # obtain input arguments
    parser = argparse.ArgumentParser(description="Test database connectivity")
    parser.add_argument('database', help='Name of database to connect to')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.info("TestRun on database %s", args.database)

    # perform basic setup
    loader = ContextTypeLoader(args.database)
    # loader = TypeLoader(args.database)
    detectors = [AlmostEqualDetector(1)]
    runner = Runner(loader, detectors)

    # start run
    results = runner.run()

    # "pretty print" the resuls
    results_sorted = sorted(results, key=lambda x: x[1].score(), reverse=True)
    pretty_print_results(args.database, results_sorted, 100)

    print("\n--------")
    print("Analyzing just one typeusage: ")
    print(runner.analyze_one(loader.gettypeusage(34747)))

    print("\n--------")
    print("Statistical Data:")
    print(runner.statisticalData)
