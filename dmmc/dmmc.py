
import logging


class Runner(object):
    def __init__(self, loader, detectors):
        self.loader = loader
        self.detectors = detectors

    def run(self):
        results_accumulated = []

        total = loader.typeusagecount()

        # go through all separators
        for separator in loader.separators():
            logging.info("Analyzing %s", separator)

            # TODO remove
            if separator[2] == '$SWITCH_TABLE$eu$cqse$check$framework$scanner$ETokenType()':
                continue

            # obtain all tus for this abstraction level
            typeusages = loader.data(separator)

            # todo note relevant data (dataset size, ....)

            # throw all anomaly detectors on the given data
            for detector in self.detectors:
                # todo time analysis and save in meta db
                results = detector.analyze(typeusages)

                # todo write out results to db - here could be smart cause of memory constraints?, but elsewhere would be cleaner
                results_accumulated += results.items()
                logging.info("%d/%d", len(results_accumulated), total)

        return results_accumulated


if __name__ == '__main__':

    import argparse

    from .database import Connector, ContextTypeLoader
    from .detectors.almostequal import AlmostEqualDetector

    parser = argparse.ArgumentParser(description="Test database connectivity")
    parser.add_argument('database', help='Name of database to connect to')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    logging.info("TestRun on database %s", args.database)

    loader = ContextTypeLoader(args.database)
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
        print("Score: %s %s", score, tu)
