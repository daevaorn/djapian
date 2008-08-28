# -*- encoding: utf-8 -*-
import datetime

from django.db import models
from django.utils.itercompat import is_iterable

# Handle the signals of Django
from django.db.models import signals
from djapian.signals import post_save, pre_delete

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

class BaseIndexer(object):
    field_class = Field

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

        signals.post_save.connect(post_save, sender=self.model)
        signals.pre_delete.connect(pre_delete, sender=self.model)
    
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

    def search(self, *args, **kwargs):
        """Query the index for `query_string` and return a HitResults instance.
        `order_by` can have the same values as Model.objects.order_by, with
        'SCORE' being the default.
        """
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError
