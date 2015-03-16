For unification and simplification Djapian allows you to put all indexer's code into special module named `index.py`. That module has to be placed into your application directory (like standard `admin.py`).

To tell Djapian load that modules you have to call `djapian.load_indexes` function somewhere in initial code.

Recommended places to call auto discovery is projects's root `urls.py`.

But you can put indexers definitions wherever you want. `index.py` is just helper conventions for more portability and reuseability.