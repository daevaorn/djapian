# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

import os
import sys
import time
from datetime import datetime
from optparse import make_option
try:
    set
except NameError:
    from sets import Set as set

from djapian.models import Change


def do_fork():
    try:
        pid = os.fork()
    except OSError, e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if pid != 0:
        os._exit(0)

    return 0


def daemonize():
    do_fork()
    do_fork()


def update_changes(verbose, timeout, once):

    while True:
        changes = Change.objects.all().order_by("-date")
        objs_count = changes.count()

        #handled_objects = set()

        if verbose:
            remain = float(objs_count)
            time_ = time.time()

        if objs_count > 0 and verbose:
            print 'There are %d objects to update' % objs_count
        # The objects must be sorted by date
        for change in changes:
            hash = change.process()
            #handled_objects.add(hash)
            change.delete()

            if verbose:
                remain -= 1
                if objs_count == 0:
                    objs_count = 1
                done = 100-(remain*100)/objs_count
                fill = '#'*int((80*done/100))
                fill += ' '*int(80-(80*done/100))
                sys.stdout.write(' \033[47m\033[31m%02.2f%%\033[34m[%s] \
\033[35m- %d objs missing\r' % (done, fill, remain))
                sys.stdout.flush()
        if verbose and objs_count > 0:
            print '\033[0;0m'

        if once:
            break

        time.sleep(timeout)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--verbosity',
                    action='store_true',
                    dest='verbosity',
                    default=False,
                    help='Verbosity output'),
        make_option("--no-fork",
                    dest="no_fork",
                    default=False,
                    action="store_true",
                    help="do not fork the process"),
        make_option("--time-out",
                    dest="timeout",
                    default=10,
                    type="int",
                    help="time to sleep between each query to the database \
(default: %default)"),
        make_option("--run-once",
                    dest="once",
                    default=False,
                    action="store_true",
                    help="run indexer one time"),
    )
    help = "This is the Djapian daemon used to update the index based on \
djapian_change table."

    requires_model_validation = True

    def handle(self, verbosity=False,
               no_fork=False, timeout=10,
               once=False, *args, **options):
        if not no_fork:
            daemonize()

        update_changes(verbosity, timeout, once)
