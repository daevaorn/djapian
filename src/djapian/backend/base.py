# -*- encoding: utf-8 -*-
import sys

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

# Handle the signals of Django
from django.db.models import signals
from django.dispatch import dispatcher
from djapian.signals import post_save, pre_delete

# For Python 2.3
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

# FIXME: Methods that accept a field parameter claim to accept Field instances
# or strings giving the object path. However, since there is no Field
# attribute giving the Model it is bound to, these methods only work for
# strings at the moment. This doesn't really affect the ease of use of the
# library, as strings are actually easier to use.

def str_to_field(string, namespace=None):
    """Gets the column attribute from the model as indicated
    by `string`, following ForeignKey attributes, etc.

    Example: 'Person.first_name' -> Person._meta.get_field('first_name')

    `namespace` is the dict-like object in which the object path will be
    searched. If None, the caller's global namespace will be used, thanks
    to the sys._getframe hack. This is important so that, for example,
    if `string` is 'models.Person.first_name', the caller's models module
    is used instead of the django.db.models module imported here.
    """
    # FIXME: This whole function is either silly or clever...
    objPath = string.split('.')
    model = None
    if namespace is None:
        # FIXME: This uses the sys._getframe hack to get the caller's namespace.
        obj = sys._getframe(1).f_globals
    else:
        obj = namespace
    getter = obj.__getitem__

    while objPath:
        objName = objPath.pop(0)

        # This might be better in a try/except block, but the respective
        # exceptions for the getters (KeyError, AttributeError,
        # FieldDoesNotExist) are already pretty descriptive...
        obj = getter(objName)

        if isinstance(obj, models.base.ModelBase):
            model = obj
            getter = model._meta.get_field
        elif isinstance(obj, models.fields.related.ForeignKey):
            model = obj.rel.to
            getter = model._meta.get_field

        # TODO: The rest of these could be more type-smart...
        elif hasattr(obj, '__getitem__'):
            getter = obj.__getitem__
        elif hasattr(obj, '__getattribute__'):
            getter = obj.__getattribute__
        else:
            getter = obj.__getattr__

    if isinstance(obj, models.base.ModelBase):
        model = obj
        obj = obj._meta.pk

    if not isinstance(obj, models.Field):
        raise ValueError("%r is not a Field object! (%r -> %r)" % \
                         (objName, string, obj))
    # FIXME: I don't think there is a way to get back to a field's Model
    # from the Field object. This makes sense from a hierarchical viewpoint,
    # but sure makes things like this harder. Hopefully setting this attribute
    # won't mess anything up...
    obj._model = model

    return obj

class PseudoField(str):
    """Dirty class used to generete a pseudo-field with the "name" attribute"""
    def __init__(self,name):
        self.name = name.split('.')[1]
    def upper(self):
        return self.name.upper()

class Indexer(object):
    def __init__(self, path, model, fields=None, attributes=None, namespace=None, **kwargs):
        """Initialize an Indexer whose index data is stored at `path`.
        `model` is the Model (or string name of the model) whose instances will
        be used as documents. Note that fields from other models can still be
        used in the index, but this model will be the one returned from search
        results.
        `fields` may be optionally initialized as an iterable of unnamed Fields.
        `attributes` may be optionally initialized as a mapping of field names
        to Fields.
        `namespace` is the dict-like object in which fields passed as object
        paths will be searched. If None, the caller's global namespace will be
        used, thanks to the sys._getframe hack.

        Example: If `fields` is ['models.Person.first_name'], it is important
        that namespace['models'] refers to the intended module and NOT the
        django.db.models module imported here.
        """
        self.model = model # Model indexed
        self.text_fields = set([]) # Simple text fields
        self.attr_fields = {} # Prefixed fields
        self.weight = {} # Weights of fields
        new_fields = []
        self.add_database = set()
        #
        # Parse fields
        #
        if isinstance(fields, (tuple, list)): # Issue #3
            #
            # For each field checks if it is a tuple or a list and add it's 
            # weight
            #
            for field in fields: 
                if isinstance(field, (tuple, list)):
                    self.add_weigth(field[0], field[1], is_prefix=False)
                    new_fields.append(field[0])
                else:
                    new_fields.append(field)
                    
        elif isinstance(fields, basestring):
            new_fields = [fields]
        
        #
        # Parse prefixed fields
        #        
        if attributes is None:
            attributes = kwargs
        else:
            # `attributes` should take precedence to `kwargs`.
            kwargs.update(attributes)
            attributes = kwargs

        for prefix in attributes:
            field = attributes[prefix]
            if isinstance(field, (tuple, list)):
                self.add_weigth(field[0], field[1], is_prefix=True)
                attributes[prefix] = field[0]
                
        if namespace is None:
            # FIXME: This uses the sys._getframe hack to get the caller's namespace.
            namespace = sys._getframe(1).f_globals

        self._prepare_path(path)
        self.path = path


        for field in new_fields:
            self.add_field(field, namespace=namespace)

        for name, field in attributes.iteritems():
            self.add_field(field, name, namespace=namespace)

        pk = self.model._meta.pk
        pk._model = self.model
        if pk not in self.text_fields and pk not in set(self.attr_fields.values()):
            self.add_field(pk, 'pk', namespace=namespace)

        # 
        # Connect to dispatcher
        #
        dispatcher.connect(receiver=post_save, signal=signals.post_save, sender=self.model)
        dispatcher.connect(receiver=pre_delete, signal=signals.pre_delete, sender=self.model)
        
    def add_field(self, field, name=None, namespace=None):
        """Add the given field to the Indexer, where `field` is either
        an object path string or a Field instance. If `name` is None,
        the field will be added to self.text_fields, otherwise it will be
        added to self.attr_fields with the given name.
        `namespace` has the same meaning as in __init__.
        """
        # FIXME: This uses the sys._getframe hack to get the caller's namespace.
        if namespace is None:
            namespace = sys._getframe(1).f_globals

        # FIXME: Detect duplicates, or user-knows-best?
        if isinstance(field, basestring):
            try:
                field = str_to_field(field,  namespace)
            except models.fields.FieldDoesNotExist:
                # TODO: How call the function here?
                # Here is the dirty solution
                field = PseudoField(field)

        if name:
            self.attr_fields[name] = field
        else:
            self.text_fields.add(field)

    def add_weigth(self, field, weight, is_prefix=False):
        '''Set to a weight for the words in the index, so those words will 
        increase the score of the document when it's hitted.
        
        `field` is the field name which receive the weight
        
        `weight` is a number which represent the weight of this word in the 
        document, be careful with this, because very higher numbers may 
        invalidate the search, here come a simple math:
            5 words with a weight of 10 will have a final weight of 50, please 
            reffer to http://www.xapian.org/docs/intro_ir.html and to 
            http://www.xapian.org/docs/apidoc/html/classXapian_1_1Document.html#3cadc734caf3d1abdbc17290d515b546 
            for a better explanation of why this happen (we set the `wdf` 
            (Within document frequency))
        
        `is_prefix` is used to say if this weight should be applied (typo?) in 
        the prefix or in the regular text
        '''
        if not isinstance(weight, int):
            raise ValueError, '`weight` must be integer'
        if not isinstance(is_prefix, bool):
            raise ValueError, '`is_prefix` must be boolean'
        
        self.weight[(field, is_prefix)] = weight
        
    def get_weight(self, field, is_prefix):
        '''Return the weight to the `field` or 1 if there is no weight setted'''
        #
        # Get the weight of the field
        # 
        if (field, is_prefix) in self.weight:
            return self.weight[(field, is_prefix)]
        else:
            return 1 # Default weight

    def remove_field(self, field=None, name=None, find_name=True, namespace=None):
        """Remove the given field from the Indexer, where `field` is either
        an object path string or a Field instance. If `name` is given,
        the field with that name is removed. If both `field` and `name`
        are given, both are removed if they refer to different fields.
        If `find_name` is True, the named fields in self.attr_fields are
        searched for `field`, otherwise only self.text_fields is searched.
        `namespace` has the same meaning as in __init__.
        """
        # FIXME: This uses the sys._getframe hack to get the caller's namespace.
        if namespace is None:
            namespace = sys._getframe(1).f_globals

        if name:
            if name in self.attr_fields:
                del self.attr_fields[name]
                return

        if field:
            if isinstance(field, basestring):
                field = str_to_field(field, namespace)

            self.text_fields.discard(field)

            if find_name:
                for name, f in self.attr_fields.items():
                    # TODO: Make sure identity is correct here
                    if f is field:
                        del self.attr_fields[name]

    def search(self, query_string, sortBy=None):
        """Query the index for `query_string` and return a HitResults instance.
        `order_by` can have the same values as Model.objects.order_by, with
        'SCORE' being the default.
        """
        raise NotImplementedError

    def index(self, document):
        raise NotImplementedError

    def update(self, force=False):
        raise NotImplementedError

    def _prepare_path(self, path):
        pass
