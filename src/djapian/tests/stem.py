from django.test import TestCase

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry

class IndexerStemTest(BaseIndexerTest, BaseTestCase):

    def test_stemmer_class(self):
        stemmer = Entry.indexer_stem.get_stemmer("en")
        self.assertEqual(stemmer("a"), "a")
        self.assertEqual(stemmer("foo"), "foo")
        self.assertEqual(stemmer("food"), "foo")

# We cannot test indexed search with a custom stemmer until Xapian will support it.
