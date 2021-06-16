from django.db import models
from django.urls import reverse
from django.db.models import CheckConstraint, Q, F
from django.utils import tree
from core.models import ResponseMode, Person,PersonRequest,Alerts
from django.contrib.postgres.fields import ArrayField
from core.models import ResponseMode, BaseModel, Person,PersonRequest
from correspondence.models import Radicate
from crum import get_current_user
import uuid


class Topic(BaseModel):
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=128, null=False)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(Topic, self).save()
    def __str__(self):
        return self.name

class InterestGroup(BaseModel):
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=128, null=False)
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(InterestGroup, self).save()
    def __str__(self):
        return self.name

class Type(models.Model):
    name = models.CharField(max_length=128,editable=False)
    description = models.CharField(blank=False, null=False, max_length=256,default='')
    asociated_icon = models.CharField(blank=False, null=False, max_length=50,default='')
    max_response_days = models.SmallIntegerField(blank=False, null=False, default=15)
    min_response_days = models.SmallIntegerField(blank=False, null=False, default=1)
    def __str__(self):
        return self.name


class SubType(models.Model):
    type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name='subtypes')
    description = models.CharField(blank=False, null=False, max_length=256,default='')
    name = models.CharField(max_length=128)
    max_response_days = models.SmallIntegerField(blank=False, null=False, default=15)
    min_response_days = models.SmallIntegerField(blank=False, null=False, default=1)
    first_alert = models.SmallIntegerField(blank=False, null=False, default=4)
    second_alert = models.SmallIntegerField(blank=False, null=False, default=9)
    third_alert = models.SmallIntegerField(blank=False, null=False, default=14)
    alerts = models.ManyToManyField(Alerts, related_name="alerts_subtype",blank=True)
    def __str__(self):
        return self.type.name + ' / ' + self.name
    
    def save(self, *args, **kwargs):
        if(self.max_response_days <= self.type.max_response_days):
            super(SubType, self).save(*args, **kwargs)
        else:
            raise Exception("max_response_days should be lower or equal to type.max_response_days")

class PQRS(models.Model):
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    pqr_type = models.ForeignKey(Type,on_delete=models.PROTECT,related_name='pqrs_object_type',null =True)
    principal_person = models.ForeignKey(Person, on_delete=models.PROTECT,related_name='pqrs_object_principal_person',null=True)
    multi_request_person = models.ManyToManyField(PersonRequest, related_name="multi_pqrs_request_person")

# Create your models here.
class PqrsContent(Radicate):
    # person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='pqr_person')
    # subject = models.CharField(max_length=256)
    data = models.TextField(max_length=2000)
    response_mode = models.ForeignKey(ResponseMode, on_delete=models.PROTECT, related_name='pqrs_response_mode')
    # number = models.TextField(max_length=30, null=False, db_index=True)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='pqr_topic', null=False, blank= False, default=None)
    interestGroup = models.ForeignKey(InterestGroup, on_delete=models.PROTECT, related_name='pqr_interest_group', null=False, blank= False, default=None)
    subtype = models.ForeignKey(SubType, on_delete=models.PROTECT, related_name='pqr_type', null=True)
    pqrsobject = models.ForeignKey(PQRS,related_name='pqr_type_object', on_delete=models.PROTECT,blank=True, null=True)
    def get_absolute_url(self):
        return reverse('pqrs_detail', args=[self.id])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # user = get_current_user()
        # if user is not None:
        #     if not self.pk:
        #         self.user_creation = user
        #     else:
        #         self.user_updated = user
        super(PqrsContent, self).save()
