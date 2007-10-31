# -*- encoding: utf-8 -*-
IMPORTED_MODULES = {}
def djapian_import(pkg):
    '''Replacement for __import__, should be used insted it.
    Here you can import a full module by passing its path, e.g.:

    django.db.connection will return the `connection` object
    '''
    if pkg in IMPORTED_MODULES:
        return IMPORTED_MODULES[pkg]
    aux = pkg.split('.')
    import_ = aux[-1]
    from_ = '.'.join(aux[0:-1])
    mod = __import__(from_,globals(),locals(),[import_])
    klass = getattr(mod,import_)
    IMPORTED_MODULES[pkg] = klass
    return klass 

__all__ = ['djapian_import']
