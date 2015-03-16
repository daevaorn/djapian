## First Draft ##

## Searching the index ##

After index has been created you can srach throught it with `Indexer.search` method.

```
resultset = Entry.indexer.search("foobar")
```

According to Xapian query language you can search by concreate tags(like "title:foo") and with boolean operators (like "foo OR bar").

### `ResultSet` object ###

`search` returns a ResultSet object that represent lazy qurty to Xapian index database.

ResultSet behaves like django `QuerySet` - it performs real query only when data is need.

ResultSet has some additional method that can customize query options.

Returbinig `ResultSet` method:

  * `prefetch()` - retrieves all linked objects to each results row.
  * `flags(flag)` -
  * `order_by(tag_name)`
  * slicing with `[start:end]`

Returning some data immidietly:

  * `count()`
  * `len(resultset)`
  * `get_corrected_query_string()`
  * getting concrete row by index `[index]`

### Paginator ###

Result set is `Paginator`-compartible, so you can easy paginte result rows:

```
from django.core.paginator import Paginator

page = Paginator(resultset, 10).page(2)
```

## Hit object ##

Each `ResultSet` row is `Hit` object. This object holds match information:

  * `precent`
  * `rank`
  * `weight`
  * `model`
  * `instance`