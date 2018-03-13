from .dmmc import Runner


class DegradedLoader(object):
    def __init__(self, loader):
        self.original_loader = loader

    def data(self):
        # todo do i need the separator function?
        # this could be an iterator returning the normal dataset + degraded method x times
        # where to plug in potentially random element? -> here in parameters! (ie do ALL degradations or only some -> how many + which?)

        # needs to pass tuple with original tu + all data? / like they did (tu.original?)
        pass


class DegradedAnalysis(object):
    def __init__(self, loader, detectors):
        degraded_loader = DegradedLoader(loader)
        # todo right now it feels like it doesn't _really_ make senes to use the Runner object, rather make own loop?
        # todo give detectors some "is anomalous" function (ie add threshold parameter to AE) and use that
        # todo give detectors tostring which describes them well such that they can easily be saved in db / textual output
        self.runner = Runner(degraded_loader, detectors)

    def run(self):
        # todo need to write out totally different things than the normal runner ->
        # todo give normal runner an optinal write out db parameter

        # iterate through data of Degraded loader until there is no more left
        # each run analyze everything, check if the degraded tu was found and record results
        pass
