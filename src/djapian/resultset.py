# -*- encoding: utf-8 -*-

class SearchQuery(object):
    def __init__(self, indexer, query_str, offset=None, limit=None,
                 order_by=None, prefetch=False, flags=None, stemming_lang=None):
        self._indexer = indexer
        self._query_str = query_str
        self._offset = offset
        self._limit = limit
        self._order_by = order_by
        self._prefetch = prefetch
        self._flags = flags
        self._stemming_lang = stemming_lang
        self._resultset_cache = None

    def _clone(self, **kwargs):
        data = {
            "indexer": self._indexer,
            "query_str": self._query_str,
            "offset": self._offset,
            "limit": self._limit,
            "order_by": self._order_by,
            "prefetch": self._prefetch,
            "flags": self._flags,
            "stemming_lang": self._stemming_lang
        }
        keys = data.keys()

        data.update(kwargs)

        #delta = set(data.keys()) - set(keys)

        #if delta:
        #    raise ValueError("Illegal params: %s" % ", ".join(list(delta)))

        return SearchQuery(**data)

    def prefetch(self):
        return self._clone(prefetch=True)

    def order_by(self, field):
        return self._clone(order_by=field)

    def flags(self, flags):
        return self._clone(flags=flags)

    def stemming(self, lang):
        return self._clone(stemming_lang=lang)

    def count(self):
        return self._clone()._get_data().get_count()

    def _get_data(self):
        if self._resultset_cache is None:
            self._resultset_cache = self._indexer._do_search(
                self._query_str,
                self._offset,
                self._limit,
                self._order_by,
                self._flags,
                self._stemming_lang
            )
            if self._prefetch:
                self._resultset_cache.prefetch()
        return self._resultset_cache

    def __iter__(self):
        return self._get_data().__iter__()

    def __len__(self):
        return len(self._get_data())

    def __getitem__(self, k):
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
                "Negative indexing is not supported."

        if self._resultset_cache is not None:
            return self._get_data()[k]
        else:
            if isinstance(k, slice):
                return self._clone(
                    offset=k.start,
                    limit=k.stop-k.start
                )
            else:
                return self._clone(
                    offset=k,
                    limit=1
                )

class ResultSet(object):
    def __init__(self, indexer, mset):
        self.indexer = indexer
        self.mset = mset
        self._hits_cache = None

    def get_count(self):
        return self.mset.get_matches_estimated()

    def prefetch(self):
        rows = self._iter_results()

        pks = dict([(r.uid, i) for r in enumerate(rows)])

        instances = self.indexer.model._default_managet(in_bulk=pks.keys())

        for uid, instance in instances.iteritems():
            self._hits_cache[pks[uid]].instance = instance

    def _iter_results(self):
        import xapian

        if self._hits_cache is None:
            self._hits_cache = []
            for match in self.mset:
                self._hits_cache.append(Hit(
                    match[xapian.MSET_DOCUMENT].get_value(UID_VALUE_NUMBER),
                    match[xapian.MSET_PERCENT],
                ))
        return self._hits_cache

    def __iter__(self):
        return self._iter_results()

class Hit(object):
    def __init__(self, uid, score, model, instance=None):
        self.uid = uid
        self.score = score
        self.model = model
        self._instance=instance

    def get_instance(self):
        if self._instance is None:
            name = self.model._meta.pk.name
            pk = self.model._meta.pk.to_python(self.uid)
            self._instance = self.model.objects.get(**{name: pk})
        return self._instance

    def set_instance(self, instance):
        self._instnace = instance

    instance = property(get_instance, set_instance)

    def __repr__(self):
        return "<Hit: Model:%s pk:%s, Score:%s>" % (self.model.__name__,
                                                   self.uid, self.score)
