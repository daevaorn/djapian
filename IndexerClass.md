# Parameters #

The `Indexer` class accept the followings parameters:

  * Default parameters
    * `fields` - Optional - List with the fields in the model to index, all the fields must be a string
    * `tags` - Optional - List with tuples of fields to index, the tuples are 2 or 3 fields with the following information: `('prefix','field',weight)` (See below for more information about `weight`)

  * Advanced parameters (everything optional)
    * `path` - Change the default location where the database must be stored
    * `stemming_lang_accessor` - Used by Xapian to Stem the words, more information at http://www.xapian.org/docs/stemming.html and [Stemming](Stemming.md)
    * `trigger` - Function that return a boolean value to decide if the record must be indexed or not (usefull when you don't want index "private" information)
    * `aliases` - Allows you have aliases to your tags, like 'titulo' in portuguese could be an alias to 'title' in english

# Little FAQ #
## Prefixed fields?? ##
Prefixed fields allows you to set prefix to yours fields, if you have a field named 'title' into your model, you can search for "title:anyword" by adding `('title':'title')` into the `tags` parameters of `Indexer` class.

## Weight?? ##
Sometimes you just want to set some priority to some fields, in a model with **title** and **content** you may want to set the **title** twice the weight of **content**, you have 2 ways to do that:

  1. In the `fields` parameter: just change the field to a tuple with `('field',weight)`
  1. In the `tags` parameter: just add the third index into the tuple of the tag: `('prefix','field',weight)`

The `weight` must always be integer, and the default is `1`, so, if you put `2` it will be twice the weight of the others fields, as well as if you put `N`, it will be `N` time more important than other fields