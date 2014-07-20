import rethinkdb as r
from rethinkdb.errors import RqlDriverError

__all__ = ['ConnectionError', 'connect', 'register_connection',
           'DEFAULT_CONNECTION_NAME']

DEFAULT_CONNECTION_NAME = 'default'


class ConnectionError(Exception):
    pass

_connection_settings = {}
_connections = {}


def register_connection(alias, name, host=None, port=None, auth_key=None, timeout=None, **kwargs):
    global _connection_settings

    conn_settings = {
        'name': name,
        'host': host or 'localhost',
        'port': port or 28015,
        'auth_key': auth_key or "",
        'timeout': timeout or 20
    }

    conn_settings.update(kwargs)
    _connection_settings[alias] = conn_settings


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    global _connections

    if alias in _connections:
        get_connection(alias=alias).close()
        del _connections[alias]


def get_connection(alias=DEFAULT_CONNECTION_NAME, reconnect=False):
    global _connections
    # Connect to the database if not already connected
    if reconnect:
        disconnect(alias)

    if alias not in _connections:
        if alias not in _connection_settings:
            msg = 'Connection with alias "%s" has not been defined' % alias
            if alias == DEFAULT_CONNECTION_NAME:
                msg = 'You have not defined a default connection'
            raise ConnectionError(msg)
        conn_settings = _connection_settings[alias].copy()

        conn_settings.pop('name', None)

        try:
            connection = None
            connection_settings_iterator = ((alias, settings.copy()) for alias, settings in _connection_settings.iteritems())
            for alias, connection_settings in connection_settings_iterator:
                connection_settings.pop('name', None)

                if conn_settings == connection_settings and _connections.get(alias, None):
                    connection = _connections[alias]
                    break

            _connections[alias] = connection if connection else r.connect(**conn_settings)
        except RqlDriverError, e:
            raise ConnectionError("Cannot connect to database %s :\n%s" % (alias, e))
    return _connections[alias]


def connect(db, alias=DEFAULT_CONNECTION_NAME, **kwargs):
    global _connections
    if alias not in _connections:
        register_connection(alias, db, **kwargs)

    return get_connection(alias)
