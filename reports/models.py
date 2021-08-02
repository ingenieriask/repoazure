from django.db import models
from django.utils import timezone

class Date(models.Model):
    date = models.DateField(default=timezone.now, null=False, blank=False)
    day = models.SmallIntegerField(default=1, blank=False, null=False)
    month = models.SmallIntegerField(default=1, blank=False, null=False)
    year = models.SmallIntegerField(default=1, blank=False, null=False)
    week = models.SmallIntegerField(default=1, blank=False, null=False)
    weekyear = models.SmallIntegerField(default=1, blank=False, null=False)

    class Meta:
        db_table = "dw_date"

class Subtype(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    type_id = models.IntegerField(default=1, blank=False, null=False)
    type_name = models.CharField(max_length=256, blank=False, null=False)

    class Meta:
        db_table = "dw_subtype"     

class PQRS(models.Model):
    subtype = models.ForeignKey(
        Subtype, on_delete=models.PROTECT, null=True, blank=True)    
    date = models.ForeignKey(
        Date, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.BigIntegerField(default=0, blank=False, null=False)

    class Meta:
        db_table = "dw_pqrs" 