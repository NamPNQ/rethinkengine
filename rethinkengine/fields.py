import datetime
import decimal
import itertools
import re
import time
import urllib2
import uuid
import warnings
from operator import itemgetter

try:
    import dateutil
except ImportError:
    dateutil = None
else:
    import dateutil.parser

from .errors import ValidationError
from .base import (BaseField, ComplexBaseField, get_document, BaseDocument)
#from .document import Document, EmbeddedDocument

from .connection import DEFAULT_CONNECTION_NAME

__all__ = ['StringField',  'URLField',  'EmailField',  'IntField',  'LongField',
           'FloatField',  'DecimalField',  'BooleanField',  'DateTimeField',
           'ComplexDateTimeField',  'EmbeddedDocumentField', 'ObjectIdField',
           'GenericEmbeddedDocumentField',  'DynamicField',  'ListField',
           'SortedListField',  'DictField',  'MapField',  'ReferenceField',
           'GenericReferenceField',  'BinaryField',  'GridFSError',
           'GridFSProxy',  'FileField',  'ImageGridFsProxy',
           'ImproperlyConfigured',  'ImageField',  'GeoPointField', 'PointField',
           'LineStringField', 'PolygonField', 'SequenceField',  'UUIDField',
           'GeoJsonBaseField']


class StringField(BaseField):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, unicode):
            return value
        try:
            value = value.decode('utf-8')
        except:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, basestring):
            self.error('StringField only accepts string values')

        if self.max_length is not None and len(value) > self.max_length:
            self.error('String value is too long')

        if self.min_length is not None and len(value) < self.min_length:
            self.error('String value is too short')

        if self.regex is not None and self.regex.match(value) is None:
            self.error('String value did not match validation regex')

    def prepare_query_value(self, op, value):
        if not isinstance(op, basestring):
            return value

        if op.lstrip('i') in ('startswith', 'endswith', 'contains', 'exact'):
            flags = 0
            if op.startswith('i'):
                flags = re.IGNORECASE
                op = op.lstrip('i')

            regex = r'%s'
            if op == 'startswith':
                regex = r'^%s'
            elif op == 'endswith':
                regex = r'%s$'
            elif op == 'exact':
                regex = r'^%s$'

            # escape unsafe characters which could lead to a re.error
            value = re.escape(value)
            value = re.compile(regex % value, flags)
        return value


class URLField(StringField):
    """A field that validates input as an URL.

    .. versionadded:: 0.3
    """

    _URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __init__(self, verify_exists=False, url_regex=None, **kwargs):
        self.verify_exists = verify_exists
        self.url_regex = url_regex or self._URL_REGEX
        super(URLField, self).__init__(**kwargs)

    def validate(self, value):
        if not self.url_regex.match(value):
            self.error('Invalid URL: %s' % value)
            return

        if self.verify_exists:
            warnings.warn(
                "The URLField verify_exists argument has intractable security "
                "and performance issues. Accordingly, it has been deprecated.",
                DeprecationWarning)
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception, e:
                self.error('This URL appears to be a broken link: %s' % e)



class EmailField(StringField):
    """A field that validates input as an E-Mail-Address.

    .. versionadded:: 0.4
    """

    EMAIL_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,253}[A-Z0-9])?\.)+[A-Z]{2,6}$', re.IGNORECASE  # domain
    )

    def validate(self, value):
        if not EmailField.EMAIL_REGEX.match(value):
            self.error('Invalid Mail-address: %s' % value)
        super(EmailField, self).validate(value)

class IntField(BaseField):
    """An 32-bit integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(IntField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = int(value)
        except:
            self.error('%s could not be converted to int' % value)

        if self.min_value is not None and value < self.min_value:
            self.error('Integer value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Integer value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return int(value)


class LongField(BaseField):
    """An 64-bit integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(LongField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = long(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = long(value)
        except:
            self.error('%s could not be converted to long' % value)

        if self.min_value is not None and value < self.min_value:
            self.error('Long value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Long value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return long(value)


class FloatField(BaseField):
    """An floating point number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(FloatField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            self.error('FloatField only accepts float values')

        if self.min_value is not None and value < self.min_value:
            self.error('Float value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Float value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return float(value)


class DecimalField(BaseField):
    """A fixed-point decimal number field.

    .. versionchanged:: 0.8
    .. versionadded:: 0.3
    """

    def __init__(self, min_value=None, max_value=None, force_string=False,
                 precision=2, rounding=decimal.ROUND_HALF_UP, **kwargs):
        """
        :param min_value: Validation rule for the minimum acceptable value.
        :param max_value: Validation rule for the maximum acceptable value.
        :param force_string: Store as a string.
        :param precision: Number of decimal places to store.
        :param rounding: The rounding rule from the python decimal libary:

            - decimal.ROUND_CEILING (towards Infinity)
            - decimal.ROUND_DOWN (towards zero)
            - decimal.ROUND_FLOOR (towards -Infinity)
            - decimal.ROUND_HALF_DOWN (to nearest with ties going towards zero)
            - decimal.ROUND_HALF_EVEN (to nearest with ties going to nearest even integer)
            - decimal.ROUND_HALF_UP (to nearest with ties going away from zero)
            - decimal.ROUND_UP (away from zero)
            - decimal.ROUND_05UP (away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise towards zero)

            Defaults to: ``decimal.ROUND_HALF_UP``

        """
        self.min_value = min_value
        self.max_value = max_value
        self.force_string = force_string
        self.precision = decimal.Decimal(".%s" % ("0" * precision))
        self.rounding = rounding

        super(DecimalField, self).__init__(**kwargs)

    def to_python(self, value):
        if value is None:
            return value

        # Convert to string for python 2.6 before casting to Decimal
        try:
            value = decimal.Decimal("%s" % value)
        except decimal.InvalidOperation:
            return value
        return value.quantize(self.precision, rounding=self.rounding)

    def to_mongo(self, value, use_db_field=True):
        if value is None:
            return value
        if self.force_string:
            return unicode(value)
        return float(self.to_python(value))

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = unicode(value)
            try:
                value = decimal.Decimal(value)
            except Exception, exc:
                self.error('Could not convert value to decimal: %s' % exc)

        if self.min_value is not None and value < self.min_value:
            self.error('Decimal value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Decimal value is too large')

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class BooleanField(BaseField):
    """A boolean field type.

    .. versionadded:: 0.1.2
    """

    def to_python(self, value):
        try:
            value = bool(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, bool):
            self.error('BooleanField only accepts boolean values')


class DateTimeField(BaseField):
    """A datetime field.

    Uses the python-dateutil library if available alternatively use time.strptime
    to parse the dates.  Note: python-dateutil's parser is fully featured and when
    installed you can utilise it to convert varing types of date formats into valid
    python datetime objects.

    Note: Microseconds are rounded to the nearest millisecond.
      Pre UTC microsecond support is effecively broken.
      Use :class:`~mongoengine.fields.ComplexDateTimeField` if you
      need accurate microsecond support.
    """

    def validate(self, value):
        new_value = self.to_mongo(value)
        if not isinstance(new_value, (datetime.datetime, datetime.date)):
            self.error(u'cannot parse date "%s"' % value)

    def to_mongo(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if callable(value):
            return value()

        if not isinstance(value, basestring):
            return None

        # Attempt to parse a datetime:
        if dateutil:
            try:
                return dateutil.parser.parse(value)
            except (TypeError, ValueError):
                return None

        # split usecs, because they are not recognized by strptime.
        if '.' in value:
            try:
                value, usecs = value.split('.')
                usecs = int(usecs)
            except ValueError:
                return None
        else:
            usecs = 0
        kwargs = {'microsecond': usecs}
        try:  # Seconds are optional, so try converting seconds first.
            return datetime.datetime(*time.strptime(value,
                                                    '%Y-%m-%d %H:%M:%S')[:6], **kwargs)
        except ValueError:
            try:  # Try without seconds.
                return datetime.datetime(*time.strptime(value,
                                                        '%Y-%m-%d %H:%M')[:5], **kwargs)
            except ValueError:  # Try without hour/minutes/seconds.
                try:
                    return datetime.datetime(*time.strptime(value,
                                                            '%Y-%m-%d')[:3], **kwargs)
                except ValueError:
                    return None

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class UUIDField(BaseField):
    """A UUID field.

    .. versionadded:: 0.6
    """
    _binary = None

    def __init__(self, binary=True, **kwargs):
        """
        Store UUID data in the database

        :param binary: if False store as a string.

        .. versionchanged:: 0.8.0
        .. versionchanged:: 0.6.19
        """
        self._binary = binary
        super(UUIDField, self).__init__(**kwargs)

    def to_python(self, value):
        if not self._binary:
            original_value = value
            try:
                if not isinstance(value, basestring):
                    value = unicode(value)
                return uuid.UUID(value)
            except:
                return original_value
        return value

    def to_mongo(self, value):
        if not self._binary:
            return unicode(value)
        elif isinstance(value, basestring):
            return uuid.UUID(value)
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        return self.to_mongo(value)

    def validate(self, value):
        if not isinstance(value, uuid.UUID):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = uuid.UUID(value)
            except Exception, exc:
                self.error('Could not convert to UUID: %s' % exc)
