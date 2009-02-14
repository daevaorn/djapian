from django.core.paginator import Paginator

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry

class PaginatorTest(BaseIndexerTest):
    def test_paginator_creation(self):
        paginator = Paginator(Entry.indexer.search("test"), 10)

        self.assertEqual(paginator.num_pages, 1)

        page = paginator.page(1)

        self.assertEqual(len(page.object_list), 2)
