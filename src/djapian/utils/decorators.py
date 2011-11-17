import xapian

def reopen_if_modified(database, num_retry=3,
                   errors=(xapian.DatabaseModifiedError,)):
    def _wrap(func):
        def _inner(*args, **kwargs):
            for n in reversed(xrange(num_retry)):
                try:
                    return func(*args, **kwargs)
                except errors:
                    if not n:
                        raise
                    database.reopen()
        return _inner
    return _wrap
