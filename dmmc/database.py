"""Responsible for talking to the databse

Returns a list of tables for the relevant separation level.
"""

# TODO build class for some type hierarchy shit

import jaydebeapi
import os
import logging
from .typeusage import TypeUsage

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

        logging.info("Connecting to database at ", db_path)
        self.conn = jaydebeapi.connect("org.hsqldb.jdbcDriver",
                                       "jdbc:hsqldb:file:" + db_path,
                                       ["SA", ""],
                                       os.path.join(current_folder, "hsqldb.jar"), )
        return

    def cursor(self):
        return self.conn.cursor()

    def close(self):
        self.conn.close()


class Type(object):
    """Provides generators for the types and their relevant data"""

    def __init__(self, dbName):
        self.dbName = dbName
        self.connector = Connector(self.dbName)
        return

    def separators(self):
        """Generator for all typenames in databse"""
        curs = self.connector.cursor()
        curs.execute('SELECT id, typename FROM type')
        for result in result_iter(curs):
            yield result

        curs.close()

    @staticmethod
    def typeusage_query():
        return 'SELECT id, class, lineNr, context FROM typeusage WHERE typeid={0[0]}'

    @staticmethod
    def call_query():
        return 'SELECT methodId FROM callList WHERE typeusageId={0}'

    def data(self, qualifier):
        """Generator for list of typeusages grouped by type"""
        curs = self.connector.cursor()
        curs.execute(self.typeusage_query().format(qualifier))
        call_cursor = self.connector.cursor()

        for result in result_iter(curs):
            # result[0] is the typeusageId
            call_cursor.execute(self.call_query().format(result[0]))
            tu = TypeUsage(result, call_cursor.fetchall())
            yield(tu)

        curs.close()
        call_cursor.close()

    def methods(self, qualifier):
        """Get all methodIds + Names for this type"""
        curs = self.connector.cursor()
        curs.execute('SELECT id, methodName FROM method WHERE typeId={0[0]}'.format(qualifier))
        ret = curs.fetchall()
        curs.close()
        return ret

    def close(self):
        self.connector.close()


class ContextType(Type):
    """Provide generators for relevant combinations of type and context"""

    def __init__(self, dbName):
        super().__init__(dbName)
        return

    def separators(self):
        # todo does this make sense like this or should I rather only change the data call to save db queries?
        curs = self.connector.cursor()
        for typeId, typename in super().separators():
            curs.execute('SELECT DISTINCT context FROM typeusage WHERE typeid={}'.format(typeId))
            for result in result_iter(curs):
                yield typeId, typename, result[0]

        curs.close()

    @staticmethod
    def typeusage_query():
        return "SELECT id, class, lineNr, context FROM typeusage WHERE typeid={0[0]} and context='{0[2]}'"


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
    test_connector(Type(args.database))

    print()
    print("----------------------------------------------")
    print()
    print("Loading Type+Context Data from", args.database)
    test_connector(ContextType(args.database), 40)
