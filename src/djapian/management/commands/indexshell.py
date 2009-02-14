import sys
import cmd
from django.core.management.base import BaseCommand

from djapian import utils
import djapian

class Command(BaseCommand):
    help = "This is the Djapian shell that provides capabilities to query indexes."

    requires_model_validation = True

    def handle(self, *args, **options):
        utils.load_indexes()

        self._list = djapian.indexer_map.items()
        self._run = True
        self._current_index = None

        if len(args):
            self._handle_use(args[0])

        while self._run:
            try:
                command = raw_input(">>> ")

                if ' ' in command:
                    command, arg = command.split(' ', 1)
                    args = [arg]
                else:
                    args = []

                try:
                    getattr(self, "_handle_%s" % command.lower())(*args)
                except AttributeError:
                    print "Unknown command"
            except (KeyboardInterrupt, EOFError):
                print "\n"
                break

    def _handle_list(self):
        """
        Lists all available indexes
        """
        for i, pair in enumerate(self._list):
            model, indexers = pair
            print "%s: `%s.%s` by:" % (i, model._meta.app_label, model._meta.object_name.lower())
            for j, indexer in enumerate(indexers):
                print "\t%s.%s: %s" % (i, j, indexer)

    def _handle_exit(self):
        """
        Exit shell
        """
        self._run = False

    def _handle_use(self, index):
        """
        Changes current index
        """
        model, indexer = map(int, index.split('.'))
        self._current_index = self._list[model][1][indexer]
        print "Using `%s by %s` index" % (self._list[model][0], self._list[model][1][indexer])

    def _handle_query(self, query):
        """
        Returns objects fetched by given query
        """
        print list(self._current_index.search(query))

    def _handle_count(self, query):
        """
        Returns count of objects fetched by given query
        """
        print self._current_index.search(query).count()

    def _handle_total(self):
        """
        Returns count of objects in index
        """
        print self._current_index.document_count()

    def _handle_listdocs(self, slice=""):
        """
        Returns count of objects in index
        """
        db = self._current_index._db.open()

        if slice:
            bits = slice.split(':')
            if len(bits) == 2:
                start, end = map(int, bits)
            else:
                start = end = int(bits[0])
        else:
            start = 1
            end = db.get_lastdocid()

        end = min(end, db.get_lastdocid())

        for i in range(start, end + 1):
            doc = db.get_document(i)
            print "doc #%s:\n\tValues (%s):" % (i, doc.values_count())
            val = doc.values_begin()

            for i in range(doc.values_count()):
                print "\t\t%s: %s" % (val.get_valueno(), val.get_value())
                val.next()

            print "\tTerms (%s):" % doc.termlist_count()
            termlist = doc.termlist_begin()

            for i in range(doc.termlist_count()):
                print termlist.get_term(),
                termlist.next()
            print "\n"

    def _handle_help(self):
        """
        Print this message
        """
        print "Command:\tDescription:"
        for name in dir(self):
            if name.startswith("_handle_"):
                method = getattr(self, name)
                print "%s\t%s" % (name[len('_handle_'):], method.__doc__.strip("\n\r"))
