#!/.../python
import os
import sys
import time
from djapian import djapian_import
from djapian.models import Change


def update_changes(verbose):
    # It's a daemon, must run forever
    while True:
        # Get all objects that has chages
        objs = Change.objects.all()
        objs_count = objs.count()
        if verbose:
            remain = float(objs_count)
            time_ = time.time()

        if objs_count > 0 and verbose:
            print 'There are %d objects to update'%objs_count
        # The objects must be sorted by date
        for obj in objs.order_by('added'):
            try:
                # Get the index module of this object
                index = djapian_import(obj.model)
            except ImportError:
                # Oops! Something goes wrong
                print 'The model "%s" could not be imported'%obj.model
                obj.delete()
                continue
            # If was deleted, don't get info from database
            if obj.is_deleted:
                index.delete(obj.did)
            else:
                try:
                    src_obj = index.model.objects.get(id=obj.did)
                    try:
                        index.update([src_obj])
                    except UnicodeDecodeError, e:
                        err = open('djapian_error.log','a')
                        err.write('The object %s raise a UnicodeDecodeError'%(unicode(obj))
                        err.close()
                except index.model.DoesNotExist:
                    pass
            # Delete the object from database
            obj.delete()

            if verbose:
                remain -= 1
                if objs_count == 0:
                    objs_count = 1
                done = 100-(remain*100)/objs_count
                fill = '#'*int((80*done/100))
                fill += ' '*int(80-(80*done/100))
                sys.stdout.write(' \033[47m\033[31m%02.2f%%\033[34m[%s] \033[35m- %d objs missing\r'%(done, fill, remain))
                sys.stdout.flush()
        if verbose and objs_count > 0:
            print '\033[0;0m'
        time.sleep(1)

def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        usage()
        sys.exit(0)
    verbose = False
    if '-v' in sys.argv or '--verbose' in sys.argv:
        verbose = True
    if '-n' in sys.argv:
        update_changes(verbose)
    else:
        if os.fork() == 0:
            update_changes(verbose)

def usage():
    print 'Usage: %s [-n]'%__file__
    print 'Where:'
    print '    -n   Not fork, run this system in foreground'

if __name__ == '__main__':
    main()
