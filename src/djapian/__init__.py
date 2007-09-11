# -*- encoding: utf-8 -*-

def djapian_import(pkg):
    '''Replacement for __import__, should be used insted it.
    Here you can import a full module by passing its path, e.g.:

    django.db.connection will return the `connection` object
    '''
    aux = pkg.split('.')
    import_ = aux[-1]
    from_ = '.'.join(aux[0:-1])
    mod = __import__(from_,globals(),locals(),[import_])
    klass = getattr(mod,import_)
    return klass 
