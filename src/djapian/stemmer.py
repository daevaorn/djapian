# -*- encoding: utf-8 -*-
from django.conf import settings
from django.utils.encoding import smart_unicode

from djapian.utils import Text

try:
    import xapian
except ImportError:
    raise ImportError("Xapian python bindings must be installed \
to use Djapian")

DEFAULT_STEMMING_LANG = getattr(settings, "DJAPIAN_STEMMING_LANG", "none")

class Stemmer(object):
    def __init__(self, instance, stemming_lang_accessor = "get_stemming_lang"):
        """ Construct a stemmer tailored for a particular model
            instance to index. """

        self.stemming_lang_accessor = stemming_lang_accessor

        language = None

        # A per-model language setting is used
        if DEFAULT_STEMMING_LANG == "multi":
            language = self._get_lang_from_model(instance)
        # Use the language defined in DJAPIAN_STEMMING_LANG
        else:
            language = DEFAULT_STEMMING_LANG

        try:
            self.stemmer = xapian.Stem(language)
        except xapian.InvalidArgumentError, e:
            print "%s; disabling stemming for this document." % e
            self.stemmer = xapian.Stem("none")

    def stem_word(self, word):
        """ Return the stemmed form of a word """
        # This is the strangeness of the Xapian API which uses the () operator
        # to stem a word
        return self.stemmer(word)

    def stem_word_for_indexing(self, word):
        """ Return the stemmed form of a word with prefix for indexing """
        # We must prefix the stemmed form of the word with Z,
        # because the QueryParser add this prefix to each stemmed
        # words when it stems a search query.
        return "Z" + self.stem_word(word)

    def _get_lang_from_model(self, path, instance):
        """ Get the language from the Django model instance we are indexing.
            The language will be obtained if an accessor called by default
            'get_stemming_lang' is defined on the model. """
        from djapian.indexer import Field
        try:
            return Field(path).resolve(instance)
        except AttributeError:
            # No language defined
            return None
