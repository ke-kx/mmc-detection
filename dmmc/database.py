"""Responsible for talking to the databse

Returns a list of tables for the relevant separation level.
"""

from collections import namedtuple

import jaydebeapi
import os
import logging
from .typeusage import Type, TypeUsage


# TODO consider the type hierarchy stuff related to the type object

def result_iter(cursor, arraysize=1000):
    """An iterator that uses fetchmany to keep memory usage down

    Source: https://code.activestate.com/recipes/137270-use-generators-for-fetching-large-db-record-sets/
    """

    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result


class Connector(object):
    """Actually connects to database"""

    def __init__(self, db_name):
        current_folder = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(current_folder, os.pardir, 'data', db_name))

        logging.debug("Connecting to database at ", db_path)
        self.conn = jaydebeapi.connect("org.hsqldb.jdbcDriver",
                                       "jdbc:hsqldb:file:" + db_path,
                                       ["SA", ""],
                                       os.path.join(current_folder, "hsqldb.jar"), )

        # check detectors.alsmostequal equality testing if changing the order!
        self.call_query = 'SELECT methodId FROM callList WHERE typeusageId={0} ORDER BY methodId'
        self.callstrings_query = 'SELECT methodname FROM callList JOIN method ON methodId = id WHERE typeusageId = {0}'

    def gettypeusage(self, id):
        curs = self.cursor()
        curs.execute('SELECT id, class, lineNr, context, typeId FROM typeusage WHERE id={0}'.format(id))
        tmp = curs.fetchone()
        curs.execute(self.call_query.format(id))
        ret = TypeUsage(tmp[:-1], [c[0] for c in curs.fetchall()], self._gettype(tmp[-1]))
        curs.close()
        ret.callstrings = self._getcallstrings(id)
        return ret

    def _getcallstrings(self, id):
        curs = self.cursor()
        curs.execute(self.callstrings_query.format(id))
        ret = curs.fetchall()
        curs.close()
        return ret

    def _gettype(self, typeId):
        curs = self.cursor()
        curs.execute('SELECT id, parentId, typename FROM type WHERE id={0}'.format(typeId))
        type = curs.fetchone()
        curs.execute('SELECT id, methodName FROM method WHERE typeid={0}'.format(typeId))
        methods = curs.fetchall()
        curs.close()
        return Type(type, methods)

    def getmethod(self, methodId):
        curs = self.cursor()
        curs.execute('SELECT methodname FROM method WHERE id = {0}'.format(methodId))
        ret = curs.fetchone()
        curs.close()
        return ret

    def typeusagecount(self):
        curs = self.cursor()
        curs.execute('SELECT COUNT(id) FROM typeusage')
        ret = curs.fetchone()
        curs.close()
        return ret[0].longValue()

    def cursor(self):
        return self.conn.cursor()

    def close(self):
        self.conn.close()


class TypeLoader(Connector):
    """Provides generators for the types and their relevant data"""

    def __init__(self, dbName):
        super().__init__(dbName)
        self.typeusage_query = 'SELECT id, class, lineNr, context FROM typeusage WHERE typeid={0.typeId}'

    def separators(self):
        """Generator for all typenames in databse"""
        Separator = namedtuple('Separator', ['typeId', 'typename'])
        curs = self.cursor()
        curs.execute('SELECT id, typename FROM type')
        for result in result_iter(curs):
            yield Separator(*result)

        curs.close()

    def data(self, qualifier):
        """Generator for list of typeusages grouped by type"""
        type = self._gettype(qualifier.typeId)

        curs = self.cursor()
        curs.execute(self.typeusage_query.format(qualifier))
        call_cursor = self.cursor()

        for result in result_iter(curs):
            # result[0] is the typeusageId
            call_cursor.execute(self.call_query.format(result[0]))
            tu = TypeUsage(result, [c[0] for c in call_cursor.fetchall()], type)
            yield(tu)

        curs.close()
        call_cursor.close()

    def methods(self, qualifier):
        """Get all methodIds + Names for this type"""
        curs = self.cursor()
        curs.execute('SELECT id, methodName FROM method WHERE typeId={0.typeId}'.format(qualifier))
        ret = curs.fetchall()
        curs.close()
        return ret


class ContextTypeLoader(TypeLoader):
    """Provide generators for relevant combinations of type and context"""

    def __init__(self, dbName):
        super().__init__(dbName)
        self.typeusage_query = "SELECT id, class, lineNr, context FROM typeusage WHERE typeid={0.typeId} and context='{0.context}'"

    def separators(self):
        Separator = namedtuple('Separator', ['typeId', 'typename', 'context'])
        # todo does this make sense like this or should I rather only change the data call to save db queries?
        curs = self.cursor()
        for typeId, typename in super().separators():
            curs.execute('SELECT DISTINCT context FROM typeusage WHERE typeid={}'.format(typeId))
            for result in result_iter(curs):
                yield Separator(typeId, typename, result[0])

        curs.close()


if __name__ == '__main__':
    """Tests"""

    import argparse
    from itertools import islice

    def test_connector(connector, num=10):
        for separator in islice(connector.separators(), num):
            print()
            print("Current separator:", separator)
            print("Complete method list:", connector.methods(separator))

            for tu in connector.data(separator):
                print(tu)

        connector.close()

    parser = argparse.ArgumentParser(description="Test database connectivity")
    parser.add_argument('database', help='Name of database to connect to')
    args = parser.parse_args()

    print("Loading Type Data from", args.database)
    test_connector(TypeLoader(args.database))

    print()
    print("----------------------------------------------")
    print()
    print("Loading Type+Context Data from", args.database)
    test_connector(ContextTypeLoader(args.database), 40)
