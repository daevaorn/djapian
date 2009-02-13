import os
import xapian

from django.conf import settings

class Database(object):
    def __init__(self, path):
        self._path = path
        self._indexes = {}

    def add_index(self, model, indexer=None, attach_as="indexer"):
        if indexer is None:
            indexer = self.create_default_indexer(model)

        indexer = indexer(self, model)

        self._indexes[model] = indexer

        if attach_as is not None:
            if hasattr(model, attach_as):
                raise ValueError("Attribute with name `%s` is already exsits" % attach_as)
            else:
                model.add_to_class(attach_as, indexer)

    def open(self, write=False):
        """
        Opens database for manipulations and returns Xapian::Enquire object
        """
        if write:
            database = xapian.WritableDatabase(
                self.path,
                xapian.DB_CREATE_OR_OPEN,
            )
        else:
            try:
                database = xapian.Database(self.path)
            except xapian.DatabaseOpeningError:
                self._create_database()

                database = xapian.Database(self.path)

        return database

    def _create_database(self):
        database = xapian.WritableDatabase(
            self.path,
            xapian.DB_CREATE_OR_OPEN,
        )
        database.close()

    def document_count(self):
        pass

    def create_default_indexer(self, model):
        pass

    def index_count(self):
        return len(self._indexes)

    def clear(self):
        pass

db = Database(settings.DJAPIAN_DATABASE_PATH)
