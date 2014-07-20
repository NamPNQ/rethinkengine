from .errors import NotRegistered

# Delete rules
DO_NOTHING = 0
NULLIFY = 1
CASCADE = 2
DENY = 3
PULL = 4

ALLOW_INHERITANCE = False
_document_registry = {}

def get_document(name):
    doc = _document_registry.get(name, None)
    if not doc:
        # Possible old style name
        single_end = name.split('.')[-1]
        compound_end = '.%s' % single_end
        possible_match = [k for k in _document_registry.keys()
                          if k.endswith(compound_end) or k == single_end]
        if len(possible_match) == 1:
            doc = _document_registry.get(possible_match.pop(), None)
    if not doc:
        raise NotRegistered("""
            `%s` has not been registered in the document registry.
            Importing the document class automatically registers it, has it
            been imported?
        """.strip() % name)
    return doc


_class_registry_cache = {}


def _import_class(cls_name):

    if cls_name in _class_registry_cache:
        return _class_registry_cache.get(cls_name)

    doc_classes = ('Document', 'DynamicEmbeddedDocument', 'EmbeddedDocument')
    field_classes = ('DictField', 'DynamicField', 'EmbeddedDocumentField',
                     'FileField', 'GenericReferenceField',
                     'GenericEmbeddedDocumentField', 'GeoPointField',
                     'PointField', 'LineStringField', 'ListField',
                     'PolygonField', 'ReferenceField', 'StringField',
                     'ComplexBaseField', 'GeoJsonBaseField')

    if cls_name in doc_classes:
        from rethinkengine import document as module
        import_classes = doc_classes
    elif cls_name in field_classes:
        from rethinkengine import fields as module
        import_classes = field_classes
    else:
        raise ValueError('No import set for: ' % cls_name)

    for cls in import_classes:
        _class_registry_cache[cls] = getattr(module, cls)

    return _class_registry_cache.get(cls_name)
