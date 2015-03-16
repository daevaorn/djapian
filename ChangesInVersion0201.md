## Changes in Djapian 2.1 ##

### Additional features ###

  * Added capability to skip indexer definition and use default
  * Added `select_related` flag to `prefetch` method of `ResultSet`
  * Added `filter` and `exclude` methods to `ResultSet`s. It allows now to filter search result by certain values of fields. Support basic lookup types: `exact`(default), `__gt`, `__gte`, `__lt`, `__lte`, `__in`.
  * Added composite indexer to performs search queries to set of indexers at once.

### Major bug fixes ###

  * Repaired per-query settings language definition