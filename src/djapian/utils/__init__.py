from django.conf import settings

DEFAULT_MAX_RESULTS = 100000
DEFAULT_WEIGHT = 1

def load_indexes():
    from djapian.utils import loading
    for app in settings.INSTALLED_APPS:
        try:
            loading.get_module(app, "index")
        except loading.NoModuleError:
            pass

def process_instance(indexer, action, instance):
    if action == "delete":
        # instance is instance id
        indexer.delete(instance)
    elif action in ("add", "edit"):
        model = instance.__class__

        if not indexer.trigger(instance):
            return

        try:
            try:
                indexer.update([instance])
            except Exception, e:
                print 'Damn it! You are trying to index a bugged model: %s' % e
        except model.DoesNotExist:
            pass
