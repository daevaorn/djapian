# -*- coding: utf-8 -*-
from django.contrib import admin

from djapian.models import Change

class ChangeAdmin(admin.ModelAdmin):
    """Set what's displayed in admin"""
    list_display = ('model', 'did', 'is_deleted', 'added')
    list_filter = ('model', 'is_deleted',)

admin.site.register(Change, ChangeAdmin)
