# -*- coding: utf-8 -*-
from django.test import TestCase

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Person

class IndexerSearchTextTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(IndexerSearchTextTest, self).setUp()
        self.result = Entry.indexer.search("text", return_objects=True)

    def test_result_count(self):
        self.assertEqual(len(self.result), 1)

    def test_result_row(self):
        result = self.result[0]

        self.assertEqual(result, self.entries[0])

    def test_result_list(self):
        self.assertEqual(list(self.result), self.entries[0:1])

    def test_score(self):
        self.assert_(self.result[0].search_data.score in (99, 100))


class ResultSetPaginationTest(TestCase):
    num_entries = 100
    per_page = 10
    num_pages = num_entries / per_page

    def setUp(self):
        p = Person.objects.create(name="Alex")

        for i in range(self.num_entries):
            Entry.objects.create(author=p, title="Entry with number %s" % i, text="foobar " * i)

        Entry.indexer.update()

        self.result = Entry.indexer.search("title:number", return_objects=True)

    def test_pagintion(self):
        from django.core.paginator import Paginator

        paginator = Paginator(self.result, self.per_page)

        self.assertEqual(paginator.num_pages, self.num_pages)

        page = paginator.page(5)
        
class AliasesTest(TestCase):
    num_entries = 10
    
    def setUp(self):
        p = Person.objects.create(name="Alex")

        for i in range(self.num_entries):
            Entry.objects.create(author=p, title="Entry with number %s" % i, text="foobar " * i)

        Entry.indexer.update()
        
        self.result = Entry.indexer.search("subject:number", return_objects=True)
        
    def test_pagintion(self):
        self.assertEqual(len(self.result), 10)
