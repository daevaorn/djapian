``#summary How to use stemming (enabling for instance the search of a plural form and getting results for the singular form)

# Introduction #

Stemming is the action of reducing a word to it's root. For instance, the words :
```
connection
connections
connective
connected
connecting
```
can all be reduced to a common root "connect". For more information, see [this document](http://www.xapian.org/docs/stemming.html).

This feature is available in Djapian since 2.0 release.

# Stemming in Djapian #

To use stemming in Djapian, you must first define a variable in the settings.py file of your Django project:

```
# For a complete list of supported languages, see :
# http://www.xapian.org/docs/apidoc/html/classXapian_1_1Stem.html#d4adbe1617ce7c54c3aa7d3d67d407bd
DJAPIAN_STEMMING_LANG = "en"
```

That's all there is to do. When Djapian detects the DJAPIAN\_STEMMING\_LANG is defined, it will use stemming when indexing the documents, and will stem the search query.

**Important** : For stemming to work, the index must be build with stemming enabled. You may have to rebuild your index if it was not build with stemming (i.e. delete the files in the directory containing the index and re-saving all objects that are to be indexed so Djapian can process them).

## Multiple-language support ##

To enable multiple-language support in Djapian, set the `DJAPIAN_STEMMING_LANG` variable in settings.py to `"multi"` :

```
DJAPIAN_STEMMING_LANG = "multi"
```

Multiple-language support is available in Djapian since SVN [revision 77](https://code.google.com/p/djapian/source/detail?r=77).

### Selecting the language to use when indexing documents ###

When `DJAPIAN_STEMMING_LANG` is defined as `"multi"`, Djapian is able to use a different language to stem each document (each database entry) to index. The language to use is obtained from the document to index, by calling `"get_stemming_lang"` on the model. If the method is not defined, the document is simply not stemmed.

Here is an example implementation of `get_stemming_lang` on a model :

```
class Movie(models.Model):
    title = models.CharFields(maxlength=300)
    lang = models.CharFields(maxlength=2)
    # ...

    def get_stemming_lang(self):
        return self.lang
```


You can change the name of this method by changing the parameter `lang_accessor` when constructing the XapianIndexer instance in your models file. For instance :

```
class Movie(models.Model):
    # ...
    lang = models.CharFields(maxlength=2)
    # ...

    def get_lang(self):
        return self.lang

import djapian

class XapianIndexer(djapian.Indexer):
    fields = ['description', 'language'],
    tags = [
       ('title', 'title'),
    ]

    # Method to be called on the model to get the language code for stemming
    stemming_lang_accessor = "get_lang" # By default, "get_stemming_lang"

search_index = djapian.add_index(Movie, XapianIndexer, attach_as="indexer")
```

### Selecting the language to use when making a query ###

You can specify the language to use when searching the index with the `stemming_lang` parameter :

```
from myappl.models import search_index

results = search_index.search("Some search query...").stemming('en')
```

#### Relation with the `DJAPIAN_STEMMING_LANG` setting ####

| **`lang` (parameter of `stemming()`) `ResultSet`'s method**  | **`DJAPIAN_STEMMING_LANG` (in `settings.py`)** | **Result** |
|:-------------------------------------------------------------|:-----------------------------------------------|:-----------|
| Defined | Defined or not defined | The query will be stemmed according to the value of `stemming_lang`. |
| Not defined (None) | Defined to a valid language (ex: 'en', 'fr'; something else than 'multi') | The query will be stemmed according to the value of `DJAPIAN_STEMMING_LANG`. |
| Not defined (None) | Defined to 'multi' | The query will not be stemmed. |
| Not defined (None) | Not defined or None | The query will not be stemmed. |

In other words, when using a single language for stemming (`DJAPIAN_STEMMING_LANG != "multi" `), the `stemming()` call is not required.

# Implementation notes #

## Xapian's stemming API -­ A simple program ##
This simple Python code illustrates how Xapian's stemming API works :

```
import xapian
st = xapian.Stem("en") # or "fr" or any other supported language
print st("dogs"), st("are"), st("running")
```

This program will print out "dog are run" on the standard output. To stem a word we use the operator ()
on an instance of the class Stem. This explain the strange syntax of `st("dogs")` to get the stem of the
word "dogs".

## Stemming the search query ##
The QueryParser class in Xapian is used to parse a query entered by the user into Query object that
Xapian can understand. For instance, the following query:

> Who let the dogs out?

Results in the following Query object:

```
QUERY: Xapian::Query((who:(pos=1) AND let:(pos=2) AND the:(pos=3) AND dogs:(pos=4) AND out:(pos=5)))
```

When using a stemming algorithm, the resulting Query object is the following:

```
QUERY: Xapian::Query((who:(pos=1) AND Zlet:(pos=2) AND Zthe:(pos=3) AND Zdog:(pos=4) AND Zout:(pos=5))
```

Observe that the word "dogs" was reduced to it's root "dog", and that all words excepted the first are now prefixed with a capital Z. This mean that in order to use stemming, the database must also be constructed with stemmed words prefixed with capital Z.

### Code example ###
This code will create a stemmed query, like the example in the previous section. Code similar to this is currently implemented in the `parse_query` function of `XapianIndexer` in `xap.py`.

```
import xapian
query_parser = xapian.QueryParser()
query_parser.set_default_op(xapian.Query.OP_AND)
query_parser.set_stemmer(xapian.Stem("en"))
query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
parsed_query = query_parser.parse_query("Who let the dogs out?")
print parsed_query
```

## Stemming at indexation time ##
In order to support both stemmed and non-stemmed search queries, Djapian indexes documents with both stemmed and non-stemmed forms. For instance, the following phrase :

> Who let the dogs out?

Results in the following terms to be indexed :

> who let the dogs out Zwho Zlet Zthe Zdog Zout