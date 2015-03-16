## Changes in Djapian 2.3 ##

Since this release Djapian requires Django 1.1

### Additional features ###

  * Added more lookup types for `filter` expressions including - `iexact`, `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `regex`, `iregex`
  * Added M2M fields enhanced handling
  * Added more infomative `list` index shell command output
  * Added results slicing for `query` index shell command
  * Refactored transaction management. Introduced new index parameters -- `--per_page` and `--commit_each`

### Major bug fixes ###

  * Fixed `use` index shell command error handling

Complete list of [resolved tickets](http://code.google.com/p/djapian/issues/list?can=1&q=milestone%3DRelease2.3&colspec=ID+Type+Status+Opened+Reporter+Priority+Milestone+Owner+Stars+Summary&cells=tiles)