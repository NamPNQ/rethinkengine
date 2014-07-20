class BaseField():
    creation_counter = 0
    auto_creation_counter = -1

    def __init__(self, db_field=None, name=None, required=False, default=None,
                 unique=False, unique_with=None, primary_key=False,
                 validation=None, choices=None, verbose_name=None,
                 help_text=None):
        self.db_field = (db_field or name) if not primary_key else 'id'

        self.required = required or primary_key
        self.default = default
        self.unique = bool(unique or unique_with)
        self.unique_with = unique_with
        self.primary_key = primary_key
        self.validation = validation
        self.choices = choices
        self.verbose_name = verbose_name
        self.help_text = help_text

        if self.db_field == 'id':
            self.creation_counter = BaseField.auto_creation_counter
            BaseField.auto_creation_counter -= 1
        else:
            self.creation_counter = BaseField.creation_counter
            BaseField.creation_counter += 1


class ComplexBaseField():
    pass


class EmbeddedDocument():
    pass


class DynamicEmbeddedDocument(EmbeddedDocument):
    pass


class NumberField(BaseField):
    pass


class StringField(BaseField):
    pass


class DateTimeField(BaseField):
    pass


class BooleanField(BaseField):
    pass


class ObjectField(BaseField):
    pass


class ArrayField(BaseField):
    pass
