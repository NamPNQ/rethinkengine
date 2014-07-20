import sys
import os

sys.path.append(os.path.abspath('..'))

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import rethinkdb
from rethinkengine import *
import rethinkengine.connection
from rethinkengine.connection import get_connection, ConnectionError


class ConnectionTest(unittest.TestCase):

    def tearDown(self):
        rethinkengine.connection._connection_settings = {}
        rethinkengine.connection._connections = {}
        rethinkengine.connection._dbs = {}


    def test_connect(self):
        """Ensure that the connect() method works properly.
        """
        connect('test')

        conn = get_connection()
        self.assertTrue(isinstance(conn, rethinkdb.net.Connection))

    def test_sharing_connections(self):
        """Ensure that connections are shared when the connection settings are exactly the same
        """
        connect('test', alias='testdb1')

        expected_connection = get_connection('testdb1')

        connect('test', alias='testdb2')
        actual_connection = get_connection('testdb2')
        self.assertEqual(expected_connection, actual_connection)


    def test_register_connection(self):
        """Ensure that connections with different aliases may be registered.
        """
        register_connection('testdb', 'rethinkenginetest2')

        self.assertRaises(ConnectionError, get_connection)
        conn = get_connection('testdb')
        self.assertTrue(isinstance(conn, rethinkdb.net.Connection))

if __name__ == '__main__':
    unittest.main()
