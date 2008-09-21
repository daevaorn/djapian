# -*- encoding: utf-8 -*-
#from datetime import datetime
import datetime
import os

from django.db import models
from django.utils.itercompat import is_iterable
from djapian.signals import post_save, pre_delete
from django.conf import settings
from django.utils.encoding import smart_unicode

from djapian.utils import Text
from djapian.resultset import ResultSet, ResultObjectSet, Hit
from djapian.stemmer import Stemmer
try:
    import xapian
except ImportError:
    raise ImportError("Xapian python bindings must be installed \
to use Djapian")

UID_VALUE_NUMBER = 1
MODEL_VALUE_NUMBER = 2
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

    def __init__(self, model, path=None, fields=None, tags=[],
                       stemming_lang_accessor="get_stemming_lang", trigger=lambda obj: True,
                       model_attr_name="indexer", aliases={}):
        """Initialize an Indexer whose index data is stored at `path`.
        `model` is the Model (or string name of the model) whose instances will
        be used as documents. Note that fields from other models can still be
        used in the index, but this model will be the one returned from search
        results.
        `fields` may be optionally initialized as an iterable of unnamed Fields.
        `attributes` may be optionally initialized as a mapping of field names
        to Fields.
        """
        self.raw_fields = [] # Simple text fields
        self.tags_fields = [] # Prefixed fields

        self.path = path
        self.trigger = trigger

        self.stemming_lang_accessor = stemming_lang_accessor
        self.add_database = set()

        self.aliases={}
        #
        # Parse fields
        #
        if isinstance(fields, (tuple, list)):
            #
            # For each field checks if it is a tuple or a list and add it's
            # weight
            #
            for field in fields:
                if isinstance(field, (tuple, list)):
                    self.add_field(field[0], field[1])
                else:
                    self.add_field(field)

        elif isinstance(fields, basestring):
            self.add_field(fields)

        #
        # Parse prefixed fields
        #
        for field in tags:
            tag, path = field[:2]
            if len(field) == 3:
                weight = field[2]
            else:
                weight = DEFAULT_WEIGHT

            self.add_field(path, weight, prefix=tag)

        if isinstance(model, basestring):
            app, name = models.split('.')

            model = models.get_model(app, name)

            if not model:#It isn't django model
                raise ValueError()

        for tag, aliases in aliases.iteritems():
            if self.has_tag(tag):
                if not isinstance(aliases, (list, tuple)):
                    aliases = (aliases,)
                self.aliases[tag] = aliases
            else:
                raise ValueError("Cannot create alias for tag %s that doesn't exist")


        self.model = model
        self.model_name = ".".join([model._meta.app_label, model._meta.object_name.lower()])

        if not self.path:
            # If no path specified we will create
            # for each model its own database
            import os
            self.path = os.path.join(*self.model_name.split('.'))

        if isinstance(model, models.Model):
            if "indexer" not in model._meta.__dict__:
                setattr(model._meta, "indexer", self)
            else:
                raise ValueError("Another indexer registered for %s" % model)

        if model_attr_name not in model.__dict__:
            setattr(model, model_attr_name, self)
        else:
            raise ValueError("Attribute with name %s is already exsits" % model_attr_name)

        models.signals.post_save.connect(post_save, sender=self.model)
        models.signals.pre_delete.connect(pre_delete, sender=self.model)

        self.values_nums = [field.prefix for field in self.tags_fields]

    def has_tag(self, name):
        for field in self.tags_fields:
            if field.prefix == name:
                return True

        return False

    def add_field(self, path, weight=DEFAULT_WEIGHT, prefix=None):
        field = self.field_class(path, weight, prefix)
        if prefix:
            self.tags_fields.append(field)
        else:
            self.raw_fields.append(field)

    def search(self, query, order_by='RELEVANCE', offset=0, limit=1000, \
                     flags=None, stemming_lang=None, return_objects=False):
        """
        flags are as defined in the Xapian API :
        http://www.xapian.org/docs/apidoc/html/classXapian_1_1QueryParser.html
        Combine multiple values with bitwise-or (|).
        """
        database = xapian.Database(self.get_full_database_path())
        for path in self.add_database:
            database.add_database(xapian.Database(path))
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
                valueno = self.free_values_start_number + \
self.values_nums.index(order_by)
            except ValueError:
                raise ValueError("Field %s cannot be used in order_by clause \
because it doen't exist in index")
            enquire.set_sort_by_value_then_relevance(valueno, ascending)

        enquire.set_query(self.parse_query(query, database,
                                           flags, stemming_lang))
        mset = enquire.get_mset(offset, limit)
        results = []
        for match in mset:
            results.append({
                'score': match[xapian.MSET_PERCENT],
                'uid': match[xapian.MSET_DOCUMENT].get_value(UID_VALUE_NUMBER),
                'model': match[xapian.MSET_DOCUMENT].get_value(
                                                         MODEL_VALUE_NUMBER),
            })
        self.mset = mset

        if return_objects:
            return ResultObjectSet(results, self)
        else:
            return ResultSet(results, self)

    def update(self, documents=None):
        '''Update the database with the documents.
        There are some default value and terms in a document:
         * Values:
           1. Used to store the ID of the document
           2. Store the model of the object (in the string format, like
              "project.app.model")
           3..10. Free

         * Terms
           UID: Used to store the ID of the document, so we can replace
                the document by the ID
        '''
        # Open Xapian Database
        database = xapian.WritableDatabase(
                    self.get_full_database_path(),
                    xapian.DB_CREATE_OR_OPEN,
                )

        # If doesnt have any document get all
        if documents is None:
            update_queue = self.model.objects.all()
        else:
            update_queue = documents

        # Get each document received
        for obj in update_queue:
            doc = xapian.Document()
            #
            # Add default terms and values
            #
            doc.add_term("UID%s" % obj._get_pk_val())
            doc.add_value(UID_VALUE_NUMBER, '%s' % obj._get_pk_val())
            doc.add_value(MODEL_VALUE_NUMBER, self.model_name)

            self.position = 1
            stemmer = Stemmer(obj, self.stemming_lang_accessor)
            self._process_raw_fields(database, obj, doc, stemmer)
            self._process_tags_fields(database, obj, doc, stemmer)

            database.replace_document("UID%s" % obj._get_pk_val(), doc)
            #FIXME: ^ may raise InvalidArgumentError when word in
            #         text larger than 255 simbols
        database.flush()
        del database

    def add_posting(self, database, doc, stemmer, posting, field, prefix=None):
        for field_v in Text().split(posting):
            field_v = field_v.lower()
            # A posting is an instance of a particular term
            # indexing the document
            # See http://www.xapian.org/docs/glossary.html
            # Index both the term and it's stemmed form
            for term in (field_v, stemmer.stem_word_for_indexing(field_v)):
                if prefix:
                    term = prefix.upper() + term
                doc.add_posting(
                    term,          # Term
                    self.position, # Position,
                    field.weight,   # Weight
                )
            database.add_spelling(field_v)
            self.position += 1

    def _process_raw_fields(self, database, obj, doc, stemmer):
        # Get each text field
        for field in self.raw_fields:
            try:
                posting = field.resolve(obj)
            except AttributeError, e:
                continue
            self.add_posting(database, doc, stemmer, posting, field)

    def _process_tags_fields(self, database, obj, doc, stemmer):
        # This is the valueno used to sort docs, the firsts 10
        # values are reserved for internal use
        valueno = 11
        # Set all prefixed fields (as value and prefixed postings)
        for field in self.tags_fields:
            # content_type is used to determine the type of the
            # data to index. This try/execpt is used to be able
            # to index data other than Django fields.
            try:
                field_value = field.resolve(obj)
            except AttributeError, e:
                continue

            try:
                content_type = obj._meta.get_field(field.path)
            except models.fields.FieldDoesNotExist:
                content_type = field_value

            values, terms = self.parse_value(field_value, content_type)

            for value in values:
                doc.add_value(valueno, value)
                valueno += 1

            for term in terms:
                doc.add_term(term)

            if not isinstance(field_value, unicode):
                field_value = smart_unicode(field_value, 'utf-8')

            self.add_posting(database, doc, stemmer,
                             field_value, field, field.prefix)

    def parse_value(self, field_value, content_type):
        values = []
        terms = []

        if isinstance(content_type, models.IntegerField) \
            or isinstance(content_type, int) or isinstance(content_type, long):
            #
            # Integer fields are stored with 12 leading zeros
            #
            values.append('%012d' % field_value)
        elif isinstance(content_type, models.BooleanField) \
            or isinstance(content_type, bool):
            #
            # Boolean fields are stored as 't' or 'f'
            #
            if field_value:
                values.append('t')
            else:
                values.append('f')
        elif isinstance(content_type, models.DateTimeField):
            #
            # DateTime fields are stored as %Y%m%d%H%M%S (better
            # sorting)
            #
            terms.append('YEAR%d' % field_value.year)
            terms.append('MONTH%d' % field_value.month)
            terms.append('DAY%d' % field_value.day)
            values.append(field_value.strftime('%Y%m%d%H%M%S'))
        else:
            try:
                values.append(str(field_value))
            except UnicodeEncodeError, e:
                if isinstance(field_value, unicode):
                    values.append(field_value.encode('utf-8'))
                else:
                    values.append(repr(field_value))

        return values, terms

    def related(self, query, count = 10, flags=None, stemming_lang=None):
        ''' Returns the related tags'''

        # Open the database
        db = xapian.Database(self.path)
        enq = xapian.Enquire(db)
        # Making the search
        enq.set_query(self.parse_query(query, db, flags, stemming_lang))
        res = enq.get_mset(0, 10)
        rset = xapian.RSet()

        for x in res:
            rset.add_document(x[xapian.MSET_DID])

        # Get the tags
        rel = enq.get_eset(100, rset)

        related_tag = []

        # List of tags
        for r in rel:
            related_tag.append(r[0])

        del_list = []
        # Making the negative list
        for p in related_tag:
            if p[0] in string.ascii_uppercase:
                del_list.append(p)

        # Removing the not permited tags from the list
        for x in del_list:
            related_tag.remove(x)

        return related_tag[:count]

    def delete(self, doc_id):
        """Delete a document from Xapian"""
        try:
            database = xapian.WritableDatabase(self.get_full_database_path(),
                                               xapian.DB_CREATE_OR_OPEN)
            database.delete_document('UID%d' % doc_id)
            del database
        except (IOError, RuntimeError, xapian.DocNotFoundError), e:
            pass

    def parse_query(self, term, db, flags=None, stemming_lang=None):
        """Parse Queries"""
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
            if hasattr(settings, "DJAPIAN_STEMMING_LANG"):
                if settings.DJAPIAN_STEMMING_LANG is not None:
                    if settings.DJAPIAN_STEMMING_LANG != "multi":
                        stemming_lang = settings.DJAPIAN_STEMMING_LANG

        if stemming_lang is not None:
            query_parser.set_stemmer(xapian.Stem(stemming_lang))
            query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

        if flags is not None:
            parsed_query = query_parser.parse_query(term, flags)
        else:
            parsed_query = query_parser.parse_query(term)

        # This will only work if the flag FLAG_SPELLING_CORRECTION is set
        self.corrected_query_string = query_parser.get_corrected_query_string()

        return parsed_query

    def get_corrected_query_string(self):
        return self.corrected_query_string

    def get_full_database_path(self):
        path = os.path.join(settings.DJAPIAN_DATABASE_PATH, self.path)
        try:
            os.makedirs(path)
        except OSError:
            pass
        return path

    def document_count(self):
        try:
            database = xapian.Database(self.get_full_database_path())
            return database.get_doccount()
        except xapian.DatabaseOpeningError:
            return 0

    def clear(self):
        path = self.get_full_database_path()
        try:
            for file_path in os.listdir(path):
                os.remove(os.path.join(path, file_path))

            os.rmdir(path)
        except OSError:
            pass
