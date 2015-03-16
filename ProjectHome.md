**If you are using Djapian please tell us about your project in reply to this [post](http://groups.google.com/group/djapian-users/browse_thread/thread/a3005b17f199d2f9)**

Use this package to allow full-text search in your Django project.

Versions compatibility matrix:

| **Djapian** | **Django** | **Xapian** |
|:------------|:-----------|:-----------|
|<= 2.2.4|1.0|1.0.2|
|<= 2.3.1|1.1|1.0.7|
|>= 2.4|1.2.1|1.2|


**Notice:** there is [an old issue](http://trac.xapian.org/ticket/185) with Xapian (< 1.0.13) in mod\_python environment. So be careful.

**Notice:** with [2.2.2](ChangesInVersion020202.md) release has been introduced database schema backward-incompatible bug fix - `Change` model has switched its `object_id` field type from integer to string.

### Features ###

Most of this features provided by Xapian itself and Djapian in this case plays role only as Django-compatible adaptation.

  * High-level DSL for indexer declaration
  * Result filtering with Django ORM like API
  * Result set compatible with standard Django `Paginator`
  * Indexing of field, method results and related model attributes
  * Entry filtering before indexing (by trigger function)
  * Results filtering with boolean lookups support
  * Term tagging
  * Spelling corrections
  * Stemming
  * Result ordering by fields
  * Indexers auto discovery
  * Index shell
  * Model changes auto tracking
  * Support for different index spaces

### Usage example ###

Assume that we have this models in our imaginary application:
```
class Person(models.Model):
    name = models.CharField(max_length=150)

    def __unicode__(self):
        return self.name

class Entry(models.Model):
    author = models.ForeignKey(Person, related_name="entries")
    title = models.CharField(max_length=250)
    created_on = models.DateTimeField(default=datetime.now)

    is_active = models.BooleanField(default=True)

    text = models.TextField()

    editors = models.ManyToManyField(Person, related_name="edited_entries")

    def headline(self):
        return "%s - %s" % (self.author, self.title)

    def __unicode__(self):
        return self.title
```
And we want to apply indexing functionality for model `Entry`. The next step is to create `Indexer` instance with proper settings. Indexer may look like this:
```
import djapian

class EntryIndexer(djapian.Indexer):
    fields=["text"]
    tags=[
        ("author",  "author.name" ),
        ("title",   "title",     3),
        ("date",    "created_on"  ),
        ("active",  "is_active"   ),
        ("editors", "editors"     )
    ]
    trigger=lambda indexer, obj: obj.is_active

djapian.space.add_index(Entry, EntryIndexer, attach_as="indexer")
```
In the django shell create some instances of models:
```
>>> p = Person.objects.create(name="Alex")
>>> Entry.objects.create(author=p, title="Test entry", text="Not large text field")
>>> Entry.objects.create(author=p, title="Another test entry", is_active=False)
>>> Entry.objects.create(author=p, title="Third small entry", text="Some another text")

>>> Entry.indexer.update()
```
Thats all! Each `Entry` instance has been indexed and now ready for search. Let's try:
```
>>> result = Entry.indexer.search('title:entry')
>>> len(result), result.count()
2, 2
>>> for row in result:
...   row.percent, row.instance.headline()
... 
99 Alex - Test entry
98 Alex - Third small entry
```

You can follow complete [Tutorial](Tutorial.md) for study Djapian basics.