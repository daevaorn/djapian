# -*- encoding: utf-8 -*-

class ResultSet(object):
    def __init__(self, hits, indexer):
        self._hits = hits
        self._indexer = indexer

    def __len__(self):
        return self._indexer.mset.get_matches_estimated()

    count = __len__

    def _get_item(self, hit):
        return XapianHit(hit, self._indexer)

    def _iterate(self):
        for hit in self._hits:
            yield XapianHit(hit, self._indexer)

    def __iter__(self):
        return self._iterate()

    def __getitem__(self, pos):
        '''Allow use index-based access'''
        return self._get_item(self._hits[pos])

    def __getslice__(self, start, end):
        '''Allows use slices to retrive the information
        WARNING: This returns a generator, not a "list"
        '''
        return self.__class__(self._hits[start:end], self._indexer)


class ResultObjectSet(ResultSet):
    def _get_item(self, hit, instance=None):
        if not instance:
            instance = self._indexer.model.objects.get(pk=hit['uid'])
        instance.search_data = XapianHit(hit, self._indexer)
        return instance

    def _iterate(self):
        pks = [hit['uid'] for hit in self._hits]
        query_set = self._indexer.model.objects.filter(pk__in=pks)

        for i, row in enumerate(query_set):
            yield self._get_item(self._hits[i], row)


class XapianHit(object):
    def __init__(self, data, indexer):
        self.indexer = indexer
        self.model = indexer.model
        self.data = data

    def get_instance(self):
        name = self.model._meta.pk.name
        pk = self.model._meta.pk.to_python(self.get_pk())
        return self.model.objects.get(**{name: pk})

    instance = property(get_instance)

    def __repr__(self):
        return "<%s: Model:%s pk:%s, Score:%s>" % (self.indexer.model_name,
                                                   self.model._meta,
                                                   self.get_pk(), self.score)
    def get_pk(self):
        return self.data['uid']

    def __getitem__(self, item):
        return self.data[item]

    def get_score(self):
        return self.data['score']

    score = property(get_score)
