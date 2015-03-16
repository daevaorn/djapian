## Changes in Djapian 2.2.2 ##

  * Changed Djapian's own Change model `object_id` field type. Because not all primary keys of tracked models could be integers this field must accept strings as well. Provided change requires you to modify underling field type in your database. If you are using some migration applications for Django it will be very simple but if not you have to manual execute SQL DDL `ALTER TABLE` statement.

### Major bug fixes ###

  * Fixed `CompositeIndexer` - it was broken after match deciders was introduced.