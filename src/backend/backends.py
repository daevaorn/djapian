from default import DefaultIndexer

try:
    from xap import XapianIndexer
except ImportError:
    print "Xapian backend will not be available due to an ImportError. " \
          "Do you have Xapian and Xapwrap installed?"

