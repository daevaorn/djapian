# -*- encoding: utf-8 -*-
"""
Here are the post_save and the pre_delete signals
"""
from djapian.models import Change

def post_save(sender, instance):
    '''Create the Change object to update the index'''
    Change(model=sender.index_model, did=instance.id).save()

def pre_delete(sender, instance):
    '''Create the Change object to update the index'''
    Change(model=sender.index_model, did=instance.id, is_deleted=True).save()
