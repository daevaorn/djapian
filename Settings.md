## Options ##

Djapian has 2 configuration options (values in your project `settings.py` file).

  * `DJAPIAN_DATABASE_PATH` (required) - required setting that tells Djapian where to store Xapian databases. That must be path to directory.

> Example:

```
 DJAPIAN_DATABASE_PATH = "/var/lib/myproject/djapian_data/"
```

**Notice:** that directory must be write-accessible for user who runs Django project and `manage.py` commands.

  * `DJAPIAN_STEMMING_LANG` (optional) - language code for default word's stemming generation. For available values see Xapian [documentation](http://xapian.org/docs/apidoc/html/classXapian_1_1Stem.html#d4adbe1617ce7c54c3aa7d3d67d407bd).

> Example:

```
 DJAPIAN_STEMMING_LANG = "en"
```