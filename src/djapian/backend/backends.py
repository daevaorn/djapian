from default import DefaultIndexer

try:
    from djapian.backend.xap import Indexer
except ImportError:
    raise  ImportError("Xapian backend will not be available due to an ImportError. " \
          "Do you have Xapian and Xapwrap installed?")
