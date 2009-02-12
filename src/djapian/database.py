import os
import xapian

class Database(object):
    def __init__(self, path):
        self.path = path

    def add_index(self, model, indexer=None):
        pass

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

        enquire = xapian.Enquire(database)

        return database, enquire

    def _create_database(self):
        database = xapian.WritableDatabase(
            self.path,
            xapian.DB_CREATE_OR_OPEN,
        )
        database.close()

db = Database(settings.DJAPIAN_DATABASE_PATH)
