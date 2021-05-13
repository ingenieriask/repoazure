from django.db import models
from django.urls import reverse

from core.models import ResponseMode, BaseModel, Person
from correspondence.models import Radicate


class Type(models.Model):
    name = models.CharField(max_length=128)
    is_active = models.BooleanField(null=False, default=True, blank=False)

    def __str__(self):
        return self.name


class SubType(models.Model):
    type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name='subtypes')
    name = models.CharField(max_length=128)
    response_days = models.SmallIntegerField(blank=False, null=False, default=15)
    first_alert = models.SmallIntegerField(blank=False, null=False, default=4)
    second_alert = models.SmallIntegerField(blank=False, null=False, default=9)
    third_alert = models.SmallIntegerField(blank=False, null=False, default=14)

    def __str__(self):
        return self.type.name+' / '+self.name


# Create your models here.

class PQR(Radicate):
    # person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='pqr_person')
    # subject = models.CharField(max_length=256)
    data = models.TextField(max_length=2000)
    # document_file = models.FileField(upload_to="uploads/", blank=False, null=True)
    response_mode = models.ForeignKey(ResponseMode, on_delete=models.PROTECT, related_name='pqrs_response_mode')
    # number = models.TextField(max_length=30, null=False, db_index=True)
    subtype = models.ForeignKey(SubType, on_delete=models.PROTECT, related_name='pqr_type', null=True)

    def get_absolute_url(self):
        return reverse('pqrs_detail', args=[self.id])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # user = get_current_user()
        # if user is not None:
        #     if not self.pk:
        #         self.user_creation = user
        #     else:
        #         self.user_updated = user
        super(PQR, self).save()
