

class TypeUsage(object):
    def __init__(self, dbrow, calls):
        self.id, self.clss, self.lineNr, self.context = dbrow
        self.calls = calls

    def __str__(self):
        return "TypeUsage: #{0}, Class: {1}:{2}, Context: {3}, calls: {4}"\
            .format(self.id, self.clss, self.lineNr, self.context, self.calls)
