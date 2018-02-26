# TODO can have some functionality for converting to vector later (depending on baseline - all methods of the relevant type)

class TypeUsage(object):
    def __init__(self, dbrow, calls):
        self.id, self.clss, self.lineNr, self.context = dbrow
        self.calls = set(calls)
        self.callstrings = None

    def __str__(self):
        calls = self.callstrings if self.callstrings else self.calls
        return "TypeUsage: #{0}, Class: {1}:{2}, Context: {3}, calls: {4}"\
            .format(self.id, self.clss, self.lineNr, self.context, calls)

    def __repr__(self):
        return "TypeUsage #{0}".format(self.id)