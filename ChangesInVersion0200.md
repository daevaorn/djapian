## Changes in Djapian 2.0 ##

### Additional features ###

  * Added lazy result sets
  * Added result objects fetching optimization
  * Added index shell for monitoring indexes - [RunningIndexShell](RunningIndexShell.md)
  * Speed improvements of index rebuild
  * More universal `Indexers` - allow index different modules - [IndexerClass](IndexerClass.md)
  * indexers auto discovery - [IndexersAutodiscovery](IndexersAutodiscovery.md)

### Major bug fixes ###

  * Result by field ordering
  * Proper terms generation for tags
  * Query string spelling correction
  * Command `--verbosity` option conflict with Django > 1.0

### Known bugs ###

  * Don't work per query stemming language difinition