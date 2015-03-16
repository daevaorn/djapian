## Content ##



## Introduction ##

Djapian provides simple way to apply full-text search to your exist applications and new ones. It has django-inspired style of API with flexible customizations of indexation and searching.

Let's go step-by-step through application creation process and discover Djapian basics. Before we start be sure that you have Djapian installed. If no read the complete guide to [Installation](Installation.md).

## Project setup ##

Now we create the project with `django-admin.py startproject test_project`. Then make some initial settings in `settings.py`:

  * Add `djapian` into your `INSTALLED_APPS`
  * Set `DJAPIAN_DATABASE_PATH`:

```
 DJAPIAN_DATABASE_PATH = './djapian_spaces/'
```

And run `./manage.py syncdb` to created needed DB tables.

## Sample application ##

Assume that we what to create application that stores some information about movies and its creators. It will have some basic entities such as person(actors and directors), statuios and movies itself. Represent each of this entities with its own Django models:

```
from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Studio(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255)
    director = models.ForeignKey(Person, related_name='director_movies')
    studio = models.ForeignKey(Studio)
    release_date = models.DateField()
    plot = models.TextField()

    cast = models.ManyToManyField(Person, related_name='cats_movies')

    def headline(self):
        return "%s by %s" % (self.title, self.director)

    def __unicode__(self):
        return self.title

```

And as every well crafted blog we want to add flexible search mechanism. For this purpose we will use Djapian.

## Creating indexers ##

First step is to describe how will your search indexes represent blog models. For that we have to write some classes derived from `djapian.Indexer` with index definitions and that ad it to global or our custom _index space_. It is recommended to store indexers definitions in `index.py` file of your application package directory (near `models.py`).

Prior to all we create index for `Studio` model:

```
from djapian import space, Indexer, CompositeIndexer

from movies.models import *

space.add_index(Studio, attach_as='indexer')
```

`space` is the global Djapian index space. Index space - the set of Djapian indexes that stores in given file system directory. Default space live in `DJAPIAN_DATABASE_PATH` path.

As you can see we don't provide explicit `Indexer` definition for `Studio` model. Because of it simplicity we can register it with default generated indexer.

For `Person` and `Movie` models we declare custom indexers:

```
class MovieIndexer(Indexer):
    fields = ['plot']
    tags = [
        ('title', 'title'),
        ('director', 'director'),
        ('release_date', 'release_date')
    ]

space.add_index(Movie, MovieIndexer, attach_as='indexer')

class PersonIndexer(Indexer):
   tags = [
       ('name', 'name'),
   ]

space.add_index(Person, PersonIndexer, attach_as='indexer')
```

To complete `Indexer` class reference read - IndexerClass.

The great feature provided by Djapian - `CompositeIndexer`. This type of indexer allows you to make search queries to multiple indexes at one and get consistent result raking. For our movie info application we join all tree just created indexer for composite `complete_indexer`:

```
complete_indexer = CompositeIndexer(Studio.indexer, Movie.indexer, Person.indexer)
```

## Initial data and index check ##

Now we have our models and indexers but they are useless without data. For this example I take information about six movies of "Star Wars" from [Wikipedia](http://wikipedia.org/). We need movies description with director, top actors and studio info.

When we fill the database with sample information next step it to create indexes. For initial indexes creation we have to run management command provided by Djapian called `index` with `--rebuild` flag:

```
$ ./manage.py index --rebuild
```

That's all. Now we have indexes and can make search queries among them. For index testing and debugging Djapian has special so called "index shell". Index shell is interactive command line application. It allows you to query available index spaces and get some additional information about results and indexes.

To invoke index shell there is Djapian command `indexshell`:

```
$ ./manage.py indexshell
```

And then in interactive shell you can call `help` to see available commands. Simple use pattern is to select needed index with `use` command (indexed identified with special 'dotted' number) and then make test search query. I want to search about `Death Star` in movies index:

```
>>> use 0.1.0
```

and then:

```
>>> query "Death Star" 10
```

Djapian loads index and provides result list with information about matching documents (objects). I get something like this:

```
[<Hit: model=movies.Movie pk=4, percent=100 rank=0 weight=0.136068754021>, <Hit: model=movies.Movie pk=6, percent=96 rank=1 weight=0.131598432828>,
<Hit: model=movies.Movie pk=3, percent=71 rank=2 weight=0.0978873037672>, <Hit: model=movies.Movie pk=5, percent=66 rank=3 weight=0.0900794241425>,
<Hit: model=movies.Movie pk=2, percent=57 rank=4 weight=0.0777061715929>, <Hit: model=movies.Movie pk=1, percent=56 rank=5 weight=0.0762643075739>]
```

## Insuring indexers loading ##

Before writing views we must ensure that defined indexers are loaded and initialized while Django serving web requests. Djapian has helper function called `load_indexes` that loads `index.py` in every installed application.

The best place to load indexers is project's `urls.py`. Just add this lines:

```
import djapian

djapian.load_indexes()

# Your url patterns declarations:
# ...
```

**Warning: due to python module importing hell it is strongly recommended to use one "import path convention". If you use project name in your import statements use it everywhere. Otherwise if you don't write project name in the beginning of import path don't do it also everywhere. Mixing of conventions will produce highly strange "bugs" and difficulties. I prefer second convention - all paths have no project name.**

## Writing search view ##

And now after all preparations we a ready write our search logic. First of all let's create our custom search form:

```
from django import forms
from django.shortcuts import render_to_response

from movies.models import *
from movies.index import complete_indexer

MODEL_MAP = {
    'studio': Studio,
    'person': Person,
    'movie': Movie
}

MODEL_CHOICES = [('', 'all')] + zip(MODEL_MAP.keys(), MODEL_MAP.keys())

class SearchForm(forms.Form):
    query = forms.CharField(required=True)
    model = forms.ChoiceField(choices=MODEL_CHOICES, required=False)
```

Our search form accepts required search query string and optionals model name.
If no model is specified("all" is chosen) search will be executed over all our indexer through composite `complete_indexer`. Otherwise search will be performed over concrete model index.

```
def search(request):
    results = []

    if request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            model = MODEL_MAP.get(form.cleaned_data['model'])

            if not model:
                indexer = complete_indexer
            else:
                indexer = model.indexer

            results = indexer.search(query).prefetch()
    else:
        form = SearchForm()

    return render_to_response('movies/search.html', {'results': results, 'form': form})
```

After view function is ready we must map it some url in project's `urls.py`:
```
from movies.views import search

# ...

    url(r'^search/$', search, name='search'),
```

## Search results template ##

As you mentioned earlier we use `search.html` template for rendering search form and its result. It is very simple and predictable:

```
<div id="search_form">
    <form action='./' method='GET'>
        {{ form.as_p }}
        <p><input type="submit" value="Search!"/></p>
    </form>
</div>
<div id="results">
{% if results %}
  <h2>Search results:</h2>
  <ol>
    {% for hit in results %}
      <li>{{ hit.instance }}- {{ hit.percent }} match</li>
    {% endfor %}
  </ol>
{% endif %}
</div>
```

For the start we draw our search form with submit button and than if there are any results iterate over hits and print instance and percentage of match.

## Adding pagination ##

Due to Djapian's `ResultSet` object compatible with standard `Paginator` it allows you to paginate results as usual.

Let's update search view to apply page number and splitting result set into pages with 5 entries on each:

```
from django.core.paginator import Paginator
...
paginator = Paginator(indexer.search(query).prefetch(), 5)
results = paginator.page(int(request.GET.get('page', 1)))
```

And we have to update source `search.html` template as well with new name - 'paged\_search.html':

```
...
<ol start={{ results.start_index }}>
   {% for hit in results.object_list %}
       <li>{{ hit.instance }}- {{ hit.percent }} match</li>
   {% endfor %}
</ol>
{% if results.has_next %}
<a href="./?query={{ form.cleaned_data.query }}&page={{ results.next_page_number }}">Next page</a>
{% endif %}
```

## Starting index daemon ##

In the lifetime of the movies application there are many cases when data will be changed: added, edited or deleted. Djapian stores change log and can update corresponding indexes with information from it.

To invoke index update process we need to run `index` command:

```
$ ./manage.py index
```

For real world projects it is recommend to run this command by some time intervals with `cron` or other task scheduling software.

## Conclusion ##

Thats all. Now you have basic knowledge about how to create Djapian powered application. To continue Djapian exploring read the references documentation and go forward to you own usage experience.