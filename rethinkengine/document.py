from rethinkengine.base import (BaseDocument, BaseDict, BaseList, ALLOW_INHERITANCE, get_document)
from rethinkengine.errors import ValidationError
from rethinkengine.connection import DEFAULT_CONNECTION_NAME
from rethinkengine import signals

__all__ = ['Document', 'EmbeddedDocument', 'DynamicDocument',
           'DynamicEmbeddedDocument', 'OperationError',
           'InvalidCollectionError', 'NotUniqueError', 'MapReduceDocument']


class InvalidCollectionError(Exception):
    pass


class Document(BaseDocument):
    def pk(self):
        """Primary key alias
        """
        def fget(self):
            return getattr(self, self._meta['id_field'])

        def fset(self, value):
            return setattr(self, self._meta['id_field'], value)
        return property(fget, fset)
    pk = pk()


    def save(self, force_insert=False, validate=True, clean=True,
         write_concern=None,  cascade=None, cascade_kwargs=None,
         _refs=None, save_condition=None, **kwargs):

        signals.pre_save.send(self.__class__, document=self)

        if validate:
            self.validate(clean=clean)

        if write_concern is None:
            write_concern = {"w": 1}

        doc = self.to_mongo()

        created = ('id' not in doc or self._created or force_insert)
