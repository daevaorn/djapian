# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

import os
import sys
import time
from datetime import datetime
from optparse import make_option

from djapian import djapian_import
from djapian.models import Change

def update_changes(verbose, timeout):
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
                        err.write('The object %s raise a UnicodeDecodeError\n'%(unicode(obj)))
                        err.close()
                    except AttributeError, e:
                        print 'You are trying to index a bugged model: %s'%(e)
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
        time.sleep(timeout)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store_true', dest='verbosity', default=False,
            help='Verbosity output'),
        make_option("--no-fork", dest="no_fork", default=False,
                    action="store_true", help="do not fork the process"),
        make_option("--time-out", dest="timeout", default=10,
            type="int", help="time to sleep between each query to the database (default: %default)"),
    )
    help = "This is the Djapian daemon used to update the index based on djapian_change table."
    
    requires_model_validation = True

    def handle(self, verbosity, no_fork, timeout, *args, **options):
        if not no_fork:
            if os.fork() <> 0:
                sys.exit(0)
            
        update_changes(verbosity, timeout)