import logging
from random import seed, sample, choice
from collections import defaultdict
from copy import deepcopy, copy
from statistics import mean, median


class DegradedLoader(object):
    type_filter_list = ['eu.cqse.check.framework.scanner.ETokenType', 'java.lang.StringBuilder']

    def __init__(self, loader):
        self.original_loader = loader

    def data(self):
        """Return a tuple of the degraded typeusage and the complete typeusage list to run the analysis on"""
        for separator in self.original_loader.separators():
            # skip filter list stuff
            if separator.typename in self.type_filter_list:
                continue

            typeusages = list(self.original_loader.data(separator))
            if len(typeusages) == 1:
                # todo make sure this isn't cheating (not even starting analysis if there is only one TU)
                continue

            logging.info("Current tu list has %d entries", len(typeusages))
            for tu in typeusages:
                typeusages_new = copy(typeusages)
                typeusages_new.remove(tu)

                for degraded_tu in self.degrade(tu):
                    yield degraded_tu, typeusages_new + [degraded_tu], separator

    def degrade(self, tu):
        # remove each call exactly once! -> more complex degraders have to overwrite this function!
        for removed_call in tu.calls:
            degraded_tu = deepcopy(tu)
            degraded_tu.calls.remove(removed_call)
            degraded_tu.removed_calls = {removed_call}
            yield degraded_tu

    def __str__(self):
        return "{0} ({1})".format(self.__class__.__name__, self.original_loader)


class MultiDegradeLoader(DegradedLoader):
    """Also degrade additional tus in the data, used for robustness testing"""
    def __init__(self, loader, degrade_additionally=2, seed_value=0):
        super().__init__(loader)
        self.degrade_additionally = degrade_additionally

        seed(seed_value)

    def data(self):
        for degraded_tu, typeusages, separator in super().data():
            # choose the tus which shall be degraded additionally (the last one is the already degraded one)
            count = min(len(typeusages) - 1, self.degrade_additionally)
            to_degrade = sample(typeusages[:-1], count)

            for deg in to_degrade:
                typeusages.remove(deg)
                # pick one randomly chosen degradation option
                typeusages.append(choice(list(self.degrade(deg))))

            yield degraded_tu, typeusages, separator

    def __str__(self):
        return "{0} (#toDegrade: {1}, {2})".format(self.__class__.__name__, self.degrade_additionally, self.original_loader)


class RemoveMethodsLoader(DegradedLoader):
    def __init__(self , loader, remove_methods=1, seed_value=0):
        super().__init__(loader)
        self.remove_methods = remove_methods

        seed(seed_value)

    def degrade(self, tu):
        # remove each call once and also #(self.remove_methods) random additional calls
        for removed_call in tu.calls:
            degraded_tu = deepcopy(tu)
            degraded_tu.calls.remove(removed_call)
            degraded_tu.removed_calls = {removed_call}

            count = min(len(degraded_tu.calls), self.remove_methods)
            to_remove = set(sample(degraded_tu.calls, count))

            degraded_tu.calls -= to_remove
            degraded_tu.removed_calls |= to_remove

            yield degraded_tu

    def __str__(self):
        return "{0} (#removeMethods: {1}, {2})".format(self.__class__.__name__, self.remove_methods, self.original_loader)


class RndDegradedLoader(DegradedLoader):
    def __init__(self, loader, calls_to_remove=1, max_runs=10):
        super().__init__(loader)

        # todo per tu/separator/...?
        self.max_runs = max_runs
        self.calls_to_remove = calls_to_remove

    def degrade(self, tu):
        # where to plug in potentially random element? -> here in parameters! (ie do ALL degradations or only some -> how many + which?)
        raise NotImplementedError("This will be a bit tricky, still a lot of decisions to be made, but see how it perferoms")


class Scores(object):
    def __init__(self):
        self.total_analyzed = 0
        # how often degraded TUs where detected as anomalous
        self.correct = 0
        # contains the running accumulation of precision and recall scores
        self.precision_score = 0
        self.recall_score = 0

    def precision(self):
        """Average precision of the whole run"""
        if self.total_analyzed == 0:
            return 0
        return self.precision_score / self.total_analyzed

    def recall(self):
        if self.total_analyzed == 0:
            return 0
        return self.recall_score / self.total_analyzed

    def f1(self):
        if self.precision() == 0 and self.recall() == 0:
            return 0
        return 2 * (self.precision() * self.recall()) / (self.precision() + self.recall())

    def __str__(self):
        ret = "Correctly detected: {0} ({1} / {2})".format(self.correct / self.total_analyzed,
                                                           self.correct, self.total_analyzed)
        ret += " - Precision: {0}".format(self.precision())
        ret += " - Recall: {0}".format(self.recall())
        ret += " - F1: {0}".format(self.f1())
        return ret


class DetectorStatistics(Scores):
    def __init__(self):
        super().__init__()

        self.strangeness_scores = []
        # precision and recall per input size
        self.scores_per_input_size = defaultdict(Scores)

    def strangeness_data(self):
        score_list = list(map(lambda x: x.score(), self.strangeness_scores))
        ret = dict()
        ret['mean'] = mean(score_list)
        ret['median'] = median(score_list)

        # todo calculate these values a bit smarter?
        ret['<.1'] = 0
        ret['>.5'] = 0
        ret['>.9'] = 0
        for s in score_list:
            if s < 0.1: ret['<.1'] += 1
            elif s > 0.5: ret['>.5'] += 1
            if s > 0.9: ret['>.9'] += 1

        ret['<.1'] /= len(score_list)
        ret['>.5'] /= len(score_list)
        ret['>.9'] /= len(score_list)

        return ret

    def __repr__(self):
        return super().__str__()

    def __str__(self):
        ret = super().__str__()
        ret += "Strangeness data: {0}\n".format(self.strangeness_data())
        ret += "\n--- Per Input Size data --- \n"
        for input_len, score in self.scores_per_input_size.items():
            ret += "Input length: {0} - {1}\n".format(input_len, score)

        return ret


class DegradedAnalysis(object):
    """ADSFasdf köasf askölf akslöadsölf haskf h"""

    def __init__(self, degraded_loader, detectors):
        self.degraded_loader = degraded_loader
        self.detectors = detectors

        self.detector_statistics = {detector: DetectorStatistics() for detector in self.detectors}
        self.data_statistics = defaultdict(list)

    def run(self):
        """Main function to start the analysis."""

        total = self.degraded_loader.original_loader.typeusagecount()
        current = 0
        old_id = 0
        old_sep = None

        # iterate through all combinations of typeusages made available by the degraded loader
        for degraded_tu, typeusages, separator in self.degraded_loader.data():

            # only collect general statistics if we switched to the next separator
            if separator != old_sep:
                old_sep = separator
                logging.info("Switched separator to %s", separator)
                self.data_statistics['tuCount'].append(len(typeusages))
                callcounts = list(map(lambda tu: len(tu.calls), typeusages))
                self.data_statistics['callCounts'].append(callcounts)

            # only increase count if we actually switched to the next TU
            if degraded_tu.id != old_id:
                current += 1
                logging.info("%d/%d", current, total)
                old_id = degraded_tu.id

            # apply each of the given detectors
            for detector in self.detectors:
                results = detector.analyze(typeusages)
                score_degraded = results[degraded_tu.id]
                statistics = self.detector_statistics[detector]

                # note the score in general for later analysis if desired (mean, median, how many low/mid/high)
                statistics.strangeness_scores += [score_degraded]
                statistics.total_analyzed += 1

                # collect data for this input size
                data_for_current_size = statistics.scores_per_input_size[len(typeusages)]
                data_for_current_size.total_analyzed += 1

                # degraded TU was correctly identified as anomalous
                if detector.is_anomalous(score_degraded):
                    statistics.correct += 1
                    data_for_current_size.correct += 1

                # update the statistics weighted with the confidence level of the predictor
                for prediction, confidence in score_degraded.predictions():
                    true_positives = len(prediction & degraded_tu.removed_calls)
                    # false_negative = len(degraded_tu.removed_calls - prediction)
                    # false_positives = len(prediction - degraded_tu.removed_calls)

                    # todo is this calculation correct? -> seems like "okay" but recall == precision for their simple thing?
                    precision = confidence * true_positives / len(prediction)
                    recall = confidence * true_positives / len(degraded_tu.removed_calls)

                    statistics.precision_score += precision
                    statistics.recall_score += recall

                    data_for_current_size.precision_score += precision
                    data_for_current_size.recall_score += recall

    def __str__(self):
        """Give a relatively useful overview of the dataset and the results"""
        # print general statistics
        ds = self.data_statistics
        ret = "---------- Dataset statistics ----------\n"
        # ret += "tuCounts: {0}".format(ds['tuCount'])

        ret += "Calllist Minimums: {0}\n".format(list(map(min, ds['callCounts'])))
        ret += "Calllist Maximums: {0}\n".format(list(map(max, ds['callCounts'])))
        ret += "Calllist Averages: {0}\n".format(list(map(mean, ds['callCounts'])))
        ret += "Calllist Medians: {0}\n".format(list(map(median, ds['callCounts'])))

        ret += "\n---------- Detectors ----------\n"
        # go through statistics of each detector
        for detector, statistics in self.detector_statistics.items():
            ret += "---"
            ret += "Results of {0}\n".format(detector)
            ret += str(statistics)
        return ret


if __name__ == "__main__":
    import pickle

    from .database import parse_arguments, ContextTypeLoader
    from .detectors.almostequal import AlmostEqualDetector
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO)

    loader = RemoveMethodsLoader(ContextTypeLoader(args.database))
    detectors = [AlmostEqualDetector(), AlmostEqualDetector(2)]
    analysis = DegradedAnalysis(loader, detectors)

    logging.info("Starting run with db {0}, loader {1} and detectors {2}".format(args.database, loader, detectors))
    analysis.run()

    # save run to pkl file!
    logging.info("Saving results to file")
    with open("output/{0}_{1}.pkl".format(args.database, loader), "wb") as output:
        # Overwrite loader to prevent PicklingError
        analysis.degraded_loader = str(analysis.degraded_loader)
        pickle.dump(analysis, output)

    logging.info("Analyzing the results!")
    print(analysis)
