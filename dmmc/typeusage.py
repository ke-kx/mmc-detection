# TODO can have some functionality for converting to vector later (depending on baseline - all methods of the relevant type)

from collections import namedtuple
import numpy as np


class Type(object):
    def __init__(self, dbrow, methods):
        self.id, self.parentId, self.name = dbrow
        self.methods = methods

    def __str__(self):
        return "Type: #{0}, Parent: #{1}, Name: {2}, Methods: {3}"\
            .format(self.id, self.parentId, self.name, self.methods)

    def __repr__(self):
        return "Type {0}(#{1})".format(self.name, self.id)


# TODO remove callstring (can infer from Type object?!)
class TypeUsage(object):
    def __init__(self, dbrow, calls, type):
        self.id, self.clss, self.lineNr, self.context = dbrow
        self.calls = set(calls)
        self.callstrings = None
        self.type = type

    def separator(self):
        Separator = namedtuple('Separator', ['typeId', 'typename', 'context'])
        return Separator(self.type.id, self.type.name, self.context)

    def vector(self):
        return np.array([(1 if m[0] in self.calls else 0) for m in self.type.methods])

    def __str__(self):
        calls = self.callstrings if self.callstrings else self.calls
        return "TypeUsage: #{0}, Class: {1}:{2}, Context: {3}, Type: {4} calls: {5}"\
            .format(self.id, self.clss, self.lineNr, self.context, self.type.name, calls)

    def __repr__(self):
        return "TypeUsage #{0}".format(self.id)