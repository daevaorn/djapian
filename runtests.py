#!/usr/bin/env python
import tempfile

from django.conf import settings
from django.core.management import call_command

settings.configure(
    INSTALLED_APPS=('django.contrib.contenttypes', 'djapian',),
    DATABASE_ENGINE='sqlite3',
    DJAPIAN_DATABASE_PATH=tempfile.mkdtemp(prefix='djapian'),
)

if __name__ == "__main__":
    call_command('test', 'djapian')
