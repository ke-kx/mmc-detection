
# Algorithm:
#   1. obtain list of outer separators (at vanilla level == types)
#   2. obtain list of inner separators (at vanilla level == contexts -> optional?)
#   3. iterate through combination of 1+2:
#       4. obtain all tus for this abstraction level
#       5. build data as makes sense (can be objects, vectors, matrices) (flexible!)
#       6. apply similarity measure (flexible!)
#       7. output strangeness score for each instance (/save, but that should be separated)
# already include write out mechanism which saves stuff to db? (last)

# Architecture:
#   build input classes somehow (types, contexts, ...)
#   Class for obtaining TU tables from DB, in dependency of some input class

#   Class for converting tables to necessary object (python object, vectors, matrices, ...)
#   similarity measure class - necessarily different for different object...
#      ---> similarity measures inherit from class for converting tables to either python objects or vectors or matrices?
#
#   driver, taking all those classes as input and just calling functions
#

# first steps:
# build general outline
# get data like #tus, #methods for per type/context analysis
#  consider mechanism such that multiple similarity measures can operate on the same data (will obviously be useful for testing later)
# also condsider timing information for similarity measure calculation -> needs to be saved somewhere

# main driver
class MMCDetector(object):
    def __init__(self):
        #TODO set all necessary objects
        return

    def run(self):

        # iterate through all input classes
        #   obtain all tus for this abstraction level
        #   build data as makes sense
        return
