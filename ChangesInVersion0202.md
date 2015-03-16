## Changes in Djapian 2.2 ##

### Additional features ###

  * Added Xapian transaction management for document update process.
  * Added support for `X` objects with `filter`/`exclude` clause - behave almost similar as `models.Q` objects.
  * Added `tags` dictionary to each `Hit` object with matched document values

### Major bug fixes ###

  * Fixed float fields storing