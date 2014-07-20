from .common import DO_NOTHING, ALLOW_INHERITANCE, _document_registry, _import_class
from .fields import BaseField, ComplexBaseField, EmbeddedDocument
from .errors import InvalidDocumentError

class DocumentMetaclass(type):
    """Metaclass for all documents.
    """

    def __new__(cls, name, bases, attrs):
        flattened_bases = cls._get_bases(bases)

        super_new = super(DocumentMetaclass, cls).__new__

        metaclass = attrs.get('my_metaclass')
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        attrs['_is_document'] = attrs.get('_is_document', False)
        if 'meta' in attrs:
            attrs['_meta'] = attrs.pop('meta')

        if '_meta' not in attrs:
            meta = MetaDict()
            for base in flattened_bases[::-1]:
                # Add any mixin metadata from plain objects
                if hasattr(base, 'meta'):
                    meta.merge(base.meta)
                elif hasattr(base, '_meta'):
                    meta.merge(base._meta)
            attrs['_meta'] = meta


        # Handle document Fields

        # Merge all fields from subclasses
        doc_fields = {}
        for base in flattened_bases[::-1]:
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)

            # Standard object mixin - merge in any Fields
            if not hasattr(base, '_meta'):
                base_fields = {}
                for attr_name, attr_value in base.__dict__.iteritems():
                    if not isinstance(attr_value, BaseField):
                        continue
                    attr_value.name = attr_name
                    if not attr_value.db_field:
                        attr_value.db_field = attr_name
                    base_fields[attr_name] = attr_value

                doc_fields.update(base_fields)

        # Discover any document fields
        field_names = {}
        for attr_name, attr_value in attrs.iteritems():
            if not isinstance(attr_value, BaseField):
                continue
            attr_value.name = attr_name
            if not attr_value.db_field:
                attr_value.db_field = attr_name
            doc_fields[attr_name] = attr_value

            # Count names to ensure no db_field redefinitions
            field_names[attr_value.db_field] = field_names.get(attr_value.db_field, 0) + 1

        # Ensure no duplicate db_fields
        duplicate_db_fields = [k for k, v in field_names.items() if v > 1]
        if duplicate_db_fields:
            msg = ("Multiple db_fields defined for: %s " %
                   ", ".join(duplicate_db_fields))
            raise InvalidDocumentError(msg)

        # Set _fields and db_field maps
        attrs['_fields'] = doc_fields
        attrs['_db_field_map'] = dict([(k, getattr(v, 'db_field', k))
                                       for k, v in doc_fields.iteritems()])
        attrs['_reverse_db_field_map'] = dict(
            (v, k) for k, v in attrs['_db_field_map'].iteritems())

        attrs['_fields_ordered'] = tuple(i[1] for i in sorted(
            (v.creation_counter, v.name)
            for v in doc_fields.itervalues()))

        #
        # Set document hierarchy
        #
        superclasses = ()
        class_name = [name]

        for base in flattened_bases:
            if (not getattr(base, '_is_base_cls', True) and
                    not getattr(base, '_meta', {}).get('abstract', True)):
                # Collate heirarchy for _cls and _subclasses
                class_name.append(base.__name__)

            if hasattr(base, '_meta'):
                # Warn if allow_inheritance isn't set and prevent
                # inheritance of classes where inheritance is set to False
                allow_inheritance = base._meta.get('allow_inheritance', ALLOW_INHERITANCE)
                if (allow_inheritance is not True and not base._meta.get('abstract')):
                    raise ValueError('Document %s may not be subclassed' % base.__name__)

        # Get superclasses from last base superclass
        document_bases = [b for b in flattened_bases if hasattr(b, '_class_name')]
        if document_bases:
            superclasses = document_bases[0]._superclasses
            superclasses += (document_bases[0]._class_name, )

        _cls = '.'.join(reversed(class_name))
        attrs['_class_name'] = _cls
        attrs['_superclasses'] = superclasses
        attrs['_subclasses'] = (_cls, )
        attrs['_types'] = attrs['_subclasses']  # TODO depreciate _types

        new_class = super_new(cls, name, bases, attrs)

        # Set _subclasses
        for base in document_bases:
            if _cls not in base._subclasses:
                base._subclasses += (_cls,)
            base._types = base._subclasses   # TODO depreciate _types

        Document, DictField = cls._import_classes()

        if issubclass(new_class, Document):
            new_class._collection = None

        # Add class to the _document_registry
        _document_registry[new_class._class_name] = new_class

        # Handle delete rules
        for field in new_class._fields.itervalues():
            f = field
            f.owner_document = new_class
            delete_rule = getattr(f, 'reverse_delete_rule', DO_NOTHING)
            if isinstance(f, ComplexBaseField) and hasattr(f, 'field'):
                delete_rule = getattr(f.field, 'reverse_delete_rule', DO_NOTHING)
                if isinstance(f, DictField) and delete_rule != DO_NOTHING:
                    msg = ("Reverse delete rules are not supported for %s (field: %s)" % (field.__class__.__name__, field.name))
                    raise InvalidDocumentError(msg)

                f = field.field

            if delete_rule != DO_NOTHING:
                if issubclass(new_class, EmbeddedDocument):
                    msg = ("Reverse delete rules are not supported for EmbeddedDocuments (field: %s)" % field.name)
                    raise InvalidDocumentError(msg)
                f.document_type.register_delete_rule(new_class, field.name, delete_rule)

            if (field.name and hasattr(Document, field.name) and
                        EmbeddedDocument not in new_class.mro()):
                msg = ("%s is a document method and not a valid field name" % field.name)
                raise InvalidDocumentError(msg)

        return new_class

    def add_to_class(self, name, value):
        setattr(self, name, value)

    @classmethod
    def _get_bases(cls, bases):
        if isinstance(bases, BasesTuple):
            return bases
        seen = []
        bases = cls.__get_bases(bases)
        unique_bases = (b for b in bases if not (b in seen or seen.append(b)))
        return BasesTuple(unique_bases)

    @classmethod
    def __get_bases(cls, bases):
        for base in bases:
            if base is object:
                continue
            yield base
            for child_base in cls.__get_bases(base.__bases__):
                yield child_base

    @classmethod
    def _import_classes(cls):
        Document = _import_class('Document')
        EmbeddedDocument = _import_class('EmbeddedDocument')
        DictField = _import_class('DictField')
        return (Document, EmbeddedDocument, DictField)


class MetaDict(dict):
    """Custom dictionary for meta classes.
    Handles the merging of set indexes
    """
    _merge_options = ('indexes',)

    def merge(self, new_options):
        for k, v in new_options.iteritems():
            if k in self._merge_options:
                self[k] = self.get(k, []) + v
            else:
                self[k] = v


class BasesTuple(tuple):
    """Special class to handle introspection of bases tuple in __new__"""
    pass
