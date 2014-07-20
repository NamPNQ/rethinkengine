import document
from document import *
import fields
from fields import *
import connection
from connection import *
import signals
from signals import *
import errors
from errors import *


__all__ = (list(document.__all__) + list(fields.__all__) + list(connection.__all__) +
           list(signals.__all__) + list(errors.__all__))

VERSION = (0, 0, 1)


def get_version():
    if isinstance(VERSION[-1], basestring):
        return '.'.join(map(str, VERSION[:-1])) + VERSION[-1]
    return '.'.join(map(str, VERSION))

__version__ = get_version()
