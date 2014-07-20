from rethinkengine import signals
from .fields import *
from .metaclasses import DocumentMetaclass



class Document(object):
    _fields = {}
    _changed_fields = {}

    my_metaclass = DocumentMetaclass
    __metaclass__ = DocumentMetaclass

    def __init__(self, **kwargs):
        self._pk = kwargs.get('pk') or 'id'

        for k in kwargs:
            if hasattr(self, k) and not kwargs[k].startswith('_'):
                self._fields[k] = kwargs[k]

    def __setattr__(self, key, value):
        if hasattr(self, key) and not key.startswith('_'):
            print key, value

    def __getattr__(self, item):
        print 'getitem', item

    @classmethod
    def __get__(cls, item):
        print '__get__', item
