# -*- encoding: utf-8 -*-
from django.db import models

class Change(models.Model):
    # Model to be used, e.g. myproject.myapp.models.Model1
    model = models.CharField(maxlength=100, db_index=True)
    # The id of register, as in myproject.myapp.models.Model1
    did = models.PositiveIntegerField()
    # Define if this object was deleted of database
    is_deleted = models.BooleanField(default=False)
    # We need sort the changes by date
    added = models.DateTimeField(auto_now_add=True, db_index=True)
        
    def __unicode__(self):
        return u'%s#%d To delete:%s, added in %s'%(self.model, self.did, self.is_deleted, self.added)

