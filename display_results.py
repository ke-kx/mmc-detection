import os
from dmmc.analysis import *


def pretty_print(analysis):
    print("Loader: {0}".format(analysis.degraded_loader))

    # todo print if necessary
    # print(analysis.data_statistics_str())

    input_size_table(analysis)


def input_size_table(analysis):
    from prettytable import PrettyTable

    for detector, statistics in analysis.detector_statistics.items():
        print("--- Results of {0} ---".format(detector))
        print("Total: ", repr(statistics))

        print("--- Per Input Size data ---")
        t = PrettyTable(["Input Size", "Detection Ratio", "Precision", "Recall", "F1"])
        t.float_format = '.4'
        for input_len, score in statistics.scores_per_input_size.items():
            t.add_row([input_len, "{0:.4f} ({1} / {2})".format(score.correct / score.total_analyzed, score.correct,
                       score.total_analyzed), score.precision(), score.recall(), score.f1()])

        t.sortby = "Input Size"
        print(t)


def draw_XYZ_graph(analysis):
    pass


if __name__ == "__main__":
    import pickle

    # loop over all analysis results in output folder
    for filename in os.listdir("output"):

        with open("output/" + filename, "rb") as input:
            analysis = pickle.load(input)

        print("--------------------------------------------------")
        print("Results for ", filename)

        pretty_print(analysis)
