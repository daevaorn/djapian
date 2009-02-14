# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.daemonize import become_daemon

import os
import sys
from datetime import datetime
from optparse import make_option

from djapian.models import Change
from djapian import utils
import djapian

@transaction.commit_manually
def update_changes(verbose, timeout, once):
    while True:
        changes = Change.objects.all().order_by("-date")
        objs_count = changes.count()

        if objs_count > 0 and verbose:
            print 'There are %d objects to update' % objs_count

        # The objects must be sorted by date
        for change in changes:
            change.process()
            change.delete()

            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()

        if verbose and objs_count > 0:
            print '\n'

        # Need to commit if using transactions (e.g. MySQL+InnoDB) since autocommit is
        # turned off by default according to PEP 249. See also:
        # http://dev.mysql.com/doc/refman/5.0/en/innodb-consistent-read-example.html
        #
        # PEP 249 states "Database modules that do not support transactions should
        #                 implement this method with void functionality".
        transaction.commit()

        if once:
            break

        time.sleep(timeout)

def rebuild(verbosity):
    for model, indexers in djapian.indexer_map.iteritems():
        for indexer in indexers:
            for obj in model._default_manager.all():
                utils.process_instance(indexer, "add", obj)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity',
                    action='store_true',
                    default=False,
                    help='Verbosity output'),
        make_option("--daemonize",
                    dest="make_daemon",
                    default=False,
                    action="store_true",
                    help="Do not fork the process"),
        make_option("--time-out",
                    dest="timeout",
                    default=10,
                    type="int",
                    help="Time to sleep between each query to the"
                         " database (default: %default)"),
        make_option("--rebuild",
                    dest="rebuild_index",
                    default=False,
                    action="store_true",
                    help="Rebuild index database"),
    )
    help = "This is the Djapian daemon used to update the index based on djapian_change table."

    requires_model_validation = True

    def handle(self, verbosity=False, make_daemon=False, timeout=10,
               rebuild_index=False, *args, **options):
        utils.load_indexes()

        if make_daemon:
            become_daemon()

        if rebuild_index:
            rebuild(verbosity)
        else:
            update_changes(verbosity, timeout, not make_daemon)
