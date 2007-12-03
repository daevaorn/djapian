import string
import xapian
from django.db import models
from datetime import datetime
from query import ResultSet, Hit
from base import Indexer

from djapian.backend.text import Text
from djapian import djapian_import

class XapianIndexer(Indexer):
    def update(self, documents=None):
        '''Update the database with the documents.
        There are some default value and terms in a document:
         * Values:
           1. Used to store the ID of the document
           2. Store the model of the object (in the string format, like "project.app.model")
           3..10. Free

         * Terms
           UID: Used to store the ID of the document, so we can replace the document by the ID
        '''
        # Open Xapian Database
        idx = xapian.WritableDatabase(self.path, xapian.DB_CREATE_OR_OPEN)

        # If doesnt have any document get all
        if documents is None:
            update_queue = self.model.objects.all()
        else:
            update_queue = documents

        # Get each document received
        for row in update_queue:
            doc = xapian.Document()
            #
            # Add default terms and values
            #
            doc.add_term("UID%d"%row.id)
            doc.add_value(1, '%d'%row.id)
            doc.add_value(2, '%s.%s'%(row.__class__.__module__, row.__class__.__name__))

            position = 1
            # Get each text field
            for field in self.text_fields:
                try:
                    posting = ''
                    # Get its value
                    field_value = getattr(row,field.name)
                    # If it's a function
                    if callable(field_value):
                        if field_value().strip() != "":
                            posting = field_value()
                    else:
                        if field_value.strip() != "":
                            posting = field_value

                    # There's no content to add
                    if not posting:
                        continue

                    for field_v in Text().split(posting):
                        doc.add_posting(
                            field_v.lower(), # Term
                            position, # Position
                            self.get_weight('.'.join((self.model._meta.object_name,field.name)), False) # Weight
                        )
                        position += 1
                except AttributeError, e:
                    print 'AttributeError: %s'%e
                    
            valueno = 11 # This is the valueno used to sort docs, the firsts 10 values are reserved for internal use
            # Set all prefixed fields (as value and prefixed postings)
            for name, field in self.attr_fields.iteritems():
                try:
                    # Get the field value based in the field name
                    field_value = getattr(row, field.name)
                    # If it's a function get it content
                    if callable(field_value):
                        field_value = str(field_value())
                    else:
                        # Issue #2
                        content_type = row._meta.get_field(field.name)
                        if isinstance(content_type, models.IntegerField):
                            #
                            # Integer fields are stored with 12 leading zeros
                            #
                            doc.add_value(valueno, '%012d'%(field_value))
                        elif isinstance(content_type, models.BooleanField):
                            #
                            # Boolean fields are stored as 't' or 'f'
                            #
                            if field_value:
                                doc.add_value(valueno, 't')
                            else:
                                doc.add_value(valueno, 'f')
                        elif isinstance(content_type, models.DateTimeField):
                            #
                            # DateTime fields are stored as %Y%m%d%H%M%S (better 
                            # sorting)
                            # 
                            doc.add_term('YEAR%d'%(field_value.year))
                            doc.add_term('MONTH%d'%(field_value.month))
                            doc.add_term('DAY%d'%(field_value.day))
                            doc.add_value(valueno, field_value.strftime('%Y%m%d%H%M%S'))
                        else:
                            try:
                                doc.add_value(valueno, str(field_value))
                            except UnicodeEncodeError, e:
                                if isinstance(field_value, unicode):
                                    doc.add_value(valueno, field_value.encode('utf-8'))
                                else:
                                    doc.add_value(valueno, repr(field_value))
                                
                                    
                    valueno += 1
                    for field_v in Text().split(unicode(field_value)):
                        try:
                            doc.add_posting(
                                '%s%s'%(name.upper(), field_v.lower()), # Term
                                position, # Position
                                self.get_weight('.'.join((self.model._meta.object_name,name)), True) # Weight
                            )
                            position += 1
                        except UnicodeDecodeError, e:
                            print u'Forgivin word "%s"'%(field_value)
                except AttributeError, e:
                    print 'AttributeError: %s'%e               
            idx.replace_document("UID%d"%(row.id), doc)
        del idx

    def search(self, query, order_by='RELEVANCE', offset=0, limit=1000):
        idx = xapian.Database(self.path)
        for path in self.add_database:
            idx.add_database(xapian.Database(path))
        enquire = xapian.Enquire(idx)

        if order_by == 'RELEVANCE':
            enquire.set_sort_by_relevance()
        else:
            ascending = False
            if isinstance(order_by, basestring) and order_by.startswith('-'):
                ascending = True

            while order_by[0] in '+-':
                order_by = order_by[1:]

            valueno = 11
            for name, v in self.attr_fields.iteritems():
                if name == order_by:
                    break
                valueno += 1
            enquire.set_sort_by_value_then_relevance(valueno, ascending)

        enquire.set_query(self.parse_query(query))
        mset = enquire.get_mset(offset, limit)
        results = []
        for match in mset:
            results.append({
                'score':match[xapian.MSET_PERCENT],
                'uid':match[xapian.MSET_DOCUMENT].get_value(1),
                'model':match[xapian.MSET_DOCUMENT].get_value(2)
            })
        self.mset = mset
        return XapianResultSet(results,self)

    def related(self, query, count = 10):
        ''' Returns the related tags'''

        # Open the database
        db = xapian.Database(self.path)
        enq = xapian.Enquire(db)
        # Making the search
        enq.set_query(self.parse_query(query))
        res = enq.get_mset(0, 10)
        rset = xapian.RSet()

        for x in res:
            rset.add_document(x[xapian.MSET_DID])

        # Get the tags
        rel = enq.get_eset(100, rset)

        related_tag = []

        # List of tags
        for  r in rel:
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
            idx = xapian.WritableDatabase(self.path, xapian.DB_CREATE_OR_OPEN)
            idx.delete_document('UID%d'%doc_id)
            del idx
        except (IOError, RuntimeError, xapian.DocNotFoundError), e:
            pass


    def parse_query(self, term):
        """Parse Queries"""
        # Instance Xapian Query Parser
        query_parser = xapian.QueryParser()

        for name, field in self.attr_fields.iteritems():
            query_parser.add_prefix(name.lower(), name.upper())

        query_parser.set_default_op(xapian.Query.OP_AND)
        return query_parser.parse_query(term)

class XapianResultSet(ResultSet):
    def __init__(self, hits, indexer):
        self._hits = hits
        self._indexer = indexer

    def __len__(self):
        return self._indexer.mset.get_matches_estimated()
    count = __len__

    def __iter__(self):
        for hit in self._hits:
            yield XapianHit(hit,self._indexer, djapian_import(hit['model']))

    def __getitem__(self,pos):
        '''Allow use index-based access'''
        return XapianHit(self._hits[pos],self._indexer, djapian_import(hit['model']))

    def __getslice__(self,start,end):
        '''Allows use slices to retrive the information
        WARNING: This returns a generator, not a "list"
        '''
        for hit in self._hits[start:end]:
            yield XapianHit(hit,self._indexer, djapian_import(hit['model']))

class XapianHit(Hit):
    def get_pk(self):
        return self.data['uid']

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get_score(self):
        return self.data['score']

    score = property(get_score)


