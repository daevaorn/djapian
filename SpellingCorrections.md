# Using the spelling correction feature of Xapian with Djapian #

Djapian provides the way to retrieve spelling corrected version of the query string. It may be useful for something list "Do you mean ..." suggestion.

To get corrected query string you have to call `search` and then enable spelling correction with `spell_correction` method.

Here is a code example:

```
>>> result = Entry.indexer.search("texte").spell_correction()
>>> result.get_corrected_query_string()
text
```