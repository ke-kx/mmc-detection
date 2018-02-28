
import logging
from collections import defaultdict
from statistics import mean, median


class Runner(object):
    def __init__(self, loader, detectors):
        self.loader = loader
        self.detectors = detectors

        self.statisticalData = defaultdict(list)

    def run(self):
        results_accumulated = []

        total = loader.typeusagecount()

        # go through all separators
        for separator in loader.separators():
                results_accumulated += self.loop(separator)
                logging.info("%d/%d", len(results_accumulated), total)

        return results_accumulated

    def loop(self, separator):
        logging.info("Analyzing %s", separator)
        results_acc = []

        # TODO remove
        # if separator.context == '$SWITCH_TABLE$eu$cqse$check$framework$scanner$ETokenType()':
        #    return []

        # obtain all tus for this abstraction level
        typeusages = list(loader.data(separator))

        # todo note relevant data (dataset size, ....)
        self.extractStatisticalData(typeusages)

        # throw all anomaly detectors on the given data
        for detector in self.detectors:
            # todo time analysis and save in meta db
            results = detector.analyze(typeusages)

            # todo write out results to db - here could be smart cause of memory constraints?, but elsewhere would be cleaner
            # todo this is not going to work right now with multiple detectors...
            results_acc += results.items()

        return results_acc

    def extractStatisticalData(self, typeusages):
        if len(typeusages) > 10:
            self.statisticalData['tuCount'].append(len(typeusages))
            callcount = list(map(lambda tu: len(tu.calls), typeusages))
            self.statisticalData['calllistMin'].append(min(callcount))
            self.statisticalData['calllistMax'].append(max(callcount))
            self.statisticalData['calllistAvg'].append(mean(callcount))
            self.statisticalData['calllistMedian'].append(median(callcount))


if __name__ == '__main__':

    import argparse

    from .database import Connector, ContextTypeLoader, TypeLoader
    from .detectors.almostequal import AlmostEqualDetector

    parser = argparse.ArgumentParser(description="Test database connectivity")
    parser.add_argument('database', help='Name of database to connect to')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    logging.info("TestRun on database %s", args.database)

    loader = ContextTypeLoader(args.database)
    loader = TypeLoader(args.database)
    detectors = [AlmostEqualDetector(1)]
    runner = Runner(loader, detectors)

    results = runner.run()

    print("")
    logging.warning("Sorting results!")
    results_sorted = sorted(results, key=lambda x: x[1].score(), reverse=True)
    print(results_sorted[:50])

    print("")
    logging.warning("First 10 ids")
    db = Connector(args.database)
    for id, score in results_sorted[:10]:
        tu = db.gettypeusage(id)
        score.setmcstrings(db)
        print(score, tu)
        print(tu.type)
        print(tu.vector())

    print("\n--------")
    print("Analyzing just one typeusage: ")
    tu = db.gettypeusage(34747)
    print(runner.loop(tu.separator()))
    print(tu.type)

    print("\n--------")
    print("Statistical Data:")
    print(runner.statisticalData)
