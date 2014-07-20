import rethinkdb as r
VERSION = (0, 0, 1)


def get_version():
    if isinstance(VERSION[-1], basestring):
        return '.'.join(map(str, VERSION[:-1])) + VERSION[-1]
    return '.'.join(map(str, VERSION))

__version__ = get_version()


class RethinkEngine(object):
    _options = {}
    _connection = None
    _models = {}

    def __init__(self, **kwargs):
        conn_settings = {
            'name': kwargs.get('db') or 'test',
            'host': kwargs.get('host') or 'localhost',
            'port': kwargs.get('port') or 28015,
            'auth_key': kwargs.get('auth_key') or ''
        }
        self._connection = r(**conn_settings)

    def get_options(self):
        return self._options

    def create_model(self, name, schema, **options):
        full_options = self._options.copy()

        for k in options:
            full_options[k] = options[k]

        if name in self._models:
            raise Exception("Cannot redefine a model")


