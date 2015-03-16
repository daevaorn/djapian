## Changes in Djapian 2.2.3 ##

### Major bug fixes ###

  * Fixed models change tracking - introduced `Change` model explicit `object_id` field to string convertion. With some DB backends raw integer values were failed to save.