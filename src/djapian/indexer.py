# -*- encoding: utf-8 -*-
#from datetime import datetime
import datetime
import os

from django.db import models
from django.utils.itercompat import is_iterable
from djapian.signals import post_save, pre_delete
from django.conf import settings
from django.utils.encoding import smart_unicode

from djapian.resultset import SearchQuery, ResultSet
from djapian.stemmer import Stemmer
try:
    import xapian
except ImportError:
    raise ImportError("Xapian python bindings must be"
                      " installed to use Djapian")

UID_VALUE_NUMBER = 1
MODEL_VALUE_NUMBER = 2
INDEXER_VALUE_NUMBER = 3

DEFAULT_WEIGHT = 1

class Field(object):
    raw_types = (int, long, float, basestring, bool,
                 datetime.time, datetime.date, datetime.datetime)

    def __init__(self, path, weight=DEFAULT_WEIGHT, prefix=None):
        self.path = path
        self.weight = weight
        self.prefix = prefix

    def resolve(self, value):
        bits = self.path.split(".")

        for bit in bits:
            try:
                value = getattr(value, bit)
            except AttributeError:
                raise

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    raise

        if isinstance(value, self.raw_types):
            return value
        elif is_iterable(value):
            return ", ".join(value)
        elif isinstance(value, models.Manager):
            return ", ".join(value.all())
        return None

class Indexer(object):
    field_class = Field
    free_values_start_number = 11

    fields = []
    tags = []
    aliases = {}
    trigger = lambda obj: True
    stemming_lang_accessor = None

    def __init__(self, db, model):
        """Initialize an Indexer whose index data is stored at `path`.
        `model` is the Model (or string name of the model) whose instances will
        be used as documents. Note that fields from other models can still be
        used in the index, but this model will be the one returned from search
        results.
        `fields` may be optionally initialized as an iterable of unnamed Fields.
        `attributes` may be optionally initialized as a mapping of field names
        to Fields.
        """
        self._db = db
        self._model = model
        self._model_name = ".".join([model._meta.app_label, model._meta.object_name.lower()])

        self.fields = [] # Simple text fields
        self.tags = [] # Prefixed fields
        self.aliases = {}

        #
        # Parse fields
        # For each field checks if it is a tuple or a list and add it's
        # weight
        #
        for field in self.__class__.fields:
            if isinstance(field, (tuple, list)):
                self.fields.append(Field(field[0], field[1]))
            else:
                self.fields.append(Field(field))

        #
        # Parse prefixed fields
        #
        for field in self.__class__.tags:
            tag, path = field[:2]
            if len(field) == 3:
                weight = field[2]
            else:
                weight = DEFAULT_WEIGHT

            self.tags.append(Field(path, weight, prefix=tag))

        for tag, aliases in self.__class__.aliases.iteritems():
            if self.has_tag(tag):
                if not isinstance(aliases, (list, tuple)):
                    aliases = (aliases,)
                self.aliases[tag] = aliases
            else:
                raise ValueError("Cannot create alias for tag `%s` that doesn't exist" % tag)

        models.signals.post_save.connect(post_save, sender=self._model)
        models.signals.pre_delete.connect(pre_delete, sender=self._model)

    def has_tag(self, name):
        for field in self.tags:
            if field.prefix == name:
                return True

        return False

    def tag_index(self, name):
        for i, field in enumerate(self.tags):
            if field.prefix == name:
                return i

        return None

    # Public Indexer interface

    def update(self, documents=None):
        """
        Update the database with the documents.
        There are some default value and terms in a document:
         * Values:
           1. Used to store the ID of the document
           2. Store the model of the object (in the string format, like
              "project.app.model")
           3. Store the indexer descriptor (module path)
           4..10. Free

         * Terms
           UID: Used to store the ID of the document, so we can replace
                the document by the ID
        """
        # Open Xapian Database
        database = self._db.open(write=True)

        # If doesnt have any document get all
        if documents is None:
            update_queue = self.model.objects.all()
        else:
            update_queue = documents

        try:
            iterator = update_queue.iterator()
        except AttributeError:
            iterator = iter(update_queue)

        valueno = self.free_values_start_number

        # Get each document received
        for obj in iterator:
            doc = xapian.Document()
            #
            # Add default terms and values
            #
            doc.add_term("UID%s" % obj._get_pk_val())
            doc.add_value(UID_VALUE_NUMBER, '%s' % obj._get_pk_val())
            doc.add_value(MODEL_VALUE_NUMBER, self.model_name)
            doc.add_value(INDEXER_VALUE_NUMBER, self.descriptor)

            stemmer = xapian.Stem(self._get_stem_language(obj))
            generator = xapian.TermGenerator()
            generator.set_database(database)
            generator.set_document(doc)

            for field in self.fields + self.tags:
                # Trying to resolve field value or skip it
                try:
                    value = field.resolve(obj)
                except AttributeError:
                    continue
                except Exception:
                    continue

                if field.prefix:
                    # If it is a model field make some postprocessing of its value
                    try:
                        content_type = self._mode._meta.get_field(field.path.split('.')[0])
                    except self._model.FieldDoesNotExist:
                        content_type = value

                    index_value = self._get_index_value(value, content_type)
                    doc.add_value(valueno, index_value)
                    valueno += 1

                generator.index_text(value, field.weight, fielf.prefix)

            database.replace_document("UID%s" % obj.pk, doc)
            #FIXME: ^ may raise InvalidArgumentError when word in
            #         text larger than 255 simbols
        database.flush()
        del database

    def search(self, query):
        return SearchQuery(self, query)

    def delete(self, doc_id):
        """
        Delete a document from index
        """
        try:
            database = self._db.open(write=True)
            database.delete_document('UID%d' % doc_id)
            del database
        except (IOError, RuntimeError, xapian.DocNotFoundError), e:
            pass

    def document_count(self):
        database = self._db.open()
        return database.get_doccount()

    __len__ = document_count

    def clear(self):
        return
        path = self.get_full_database_path()
        try:
            for file_path in os.listdir(path):
                os.remove(os.path.join(path, file_path))

            os.rmdir(path)
        except OSError:
            pass

    # Private Indexer interface

    def _do_search(self, query, offset=None, limit=None, order_by='RELEVANCE',
                     flags=None, stemming_lang=None):
        """
        flags are as defined in the Xapian API :
        http://www.xapian.org/docs/apidoc/html/classXapian_1_1QueryParser.html
        Combine multiple values with bitwise-or (|).
        """
        database = self._db.open()
        enquire = xapian.Enquire(database)

        if order_by == 'RELEVANCE':
            enquire.set_sort_by_relevance()
        else:
            ascending = False
            if isinstance(order_by, basestring) and order_by.startswith('-'):
                ascending = True

            if order_by[0] in '+-':
                order_by = order_by[1:]

            try:
                valueno = self.free_values_start_number + self.tag_index(order_by)
            except (ValueError, TypeError):
                raise ValueError("Field %s cannot be used in order_by clause"
                                 " because it doen't exist in index" % order_by)
            enquire.set_sort_by_value_then_relevance(valueno, ascending)

        enquire.set_query(
            self._parse_query(query, database, flags, stemming_lang)
        )

        return ResultSet(self, enquire.get_mset(offset, limit))

    def _get_stem_language(self, obj):
        """
        Returns stemmig language for given object if acceptable or model wise
        """
        language = getattr(settings, "DJAPIAN_STEMMING_LANG", "none") # Use the language defined in DJAPIAN_STEMMING_LANG

        # A per-model language setting is used
        if language == "multi":
            try:
                language = Field(self.stemming_lang_accessor).resolve(obj)
            except AttributeError:
                # No language defined
                pass

        return language

    def _get_index_value(self, field_value, content_type):
        """
        Generates index values (for sorting) for given field value and its content type
        """
        value = field_value

        if isinstance(content_type, (models.IntegerField, int, long)):
            #
            # Integer fields are stored with 12 leading zeros
            #
            value = '%012d' % field_value
        elif isinstance(content_type, (models.BooleanField, bool)):
            #
            # Boolean fields are stored as 't' or 'f'
            #
            if field_value:
                value = 't'
            else:
                value = 'f'
        elif isinstance(content_type, (models.DateTimeField, datetime.datetime)):
            #
            # DateTime fields are stored as %Y%m%d%H%M%S (better
            # sorting)
            #
            value = field_value.strftime('%Y%m%d%H%M%S')

        return value

    def _parse_query(self, term, db, flags=None, stemming_lang=None):
        """
        Parses search queries
        """
        # Instance Xapian Query Parser
        query_parser = xapian.QueryParser()

        for field in self.tags_fields:
            query_parser.add_prefix(field.prefix.lower(), field.prefix.upper())
            if field.prefix in self.aliases:
                for alias in self.aliases[field.prefix]:
                    query_parser.add_prefix(alias, field.prefix.upper())

        query_parser.set_database(db)
        query_parser.set_default_op(xapian.Query.OP_AND)

        # Stemming
        # See http://code.google.com/p/djapian/wiki/Stemming
        # The stemming_lang parameter has priority; if it is
        # defined, it is used.
        # If not, the DJAPIAN_STEMMING_LANG variable from settings.py is used,
        # if it is defined, not None, and not defined as "multi" (i.e. if it is
        # defined as a language such as 'en' or 'french')
        if stemming_lang is None:
            stemming_lang = getattr(settings, "DJAPIAN_STEMMING_LANG", None)

        if stemming_lang not in (None, "multi"):
            query_parser.set_stemmer(xapian.Stem(stemming_lang))
            query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

        if flags is not None:
            parsed_query = query_parser.parse_query(term, flags)
        else:
            parsed_query = query_parser.parse_query(term)

        # This will only work if the flag FLAG_SPELLING_CORRECTION is set
        self.corrected_query_string = query_parser.get_corrected_query_string()

        return parsed_query
