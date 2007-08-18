import string
import xapian
from django.db import models
from datetime import datetime
from query import ResultSet, Hit
from base import Indexer

from djapian.backend.text import Text

class XapianIndexer(Indexer):
    def update(self, documents=None):
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
            position = 1
            # Get each text field
            for field in self.text_fields:
                posting = ''
                # Get it value
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
                    doc.add_posting(field_v, position)
                    position += 1

            valueno = 1 # This is the valueno used to sort docs
            # Set all prefixed fields (as value and prefixed postings)
            for name, field in self.attr_fields.iteritems():
                # Get the field value based in the field name
                field_value = getattr(row, field.name)
                # If it's a function get it content
                if callable(field_value):
                    field_value = str(field_value())
                else:
                    field_value = str(field_value)

                # Keys used for sort
                doc.add_value(valueno, field_value)
                valueno += 1

                for field_v in Text().split(field_value):
                    doc.add_posting('%s%s'%(name.upper(), field_v), position)
                    position += 1

            idx.replace_document(row.id, doc)
        del idx

    def search(self, query, order_by='-date', offset=0, limit=1000):
        idx = xapian.Database(self.path)
        enquire = xapian.Enquire(idx)

        if order_by == 'RELEVANCE':
            enquire.set_sort_by_relevance()
        else:
            ascending = False
            if isinstance(order_by, basestring) and order_by.startswith('-'):
                ascending = True

            while order_by[0] in '+-':
                order_by = order_by[1:]

            valueno = 1
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
                'uid':match[xapian.MSET_DID]
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
            idx.delete_document(doc_id)
            del idx
        except (IOError, RuntimeError):
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

    def __iter__(self):
        for hit in self._hits:
            yield XapianHit(hit,self._indexer)

    def __getitem__(self,pos):
        '''Allow use index-based access'''
        return XapianHit(self._hits[pos],self._indexer)

    def __getslice__(self,start,end):
        '''Allows use slices to retrive the information
        WARNING: This returns a generator, not a "list"
        '''
        for hit in self._hits[start:end]:
            yield XapianHit(hit,self._indexer)

class XapianHit(Hit):
    def get_pk(self):
        # FIXME: Hardcoded 'pk' field.
        return self.data['uid']

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get_score(self):
        return self.data['score']

    score = property(get_score)


