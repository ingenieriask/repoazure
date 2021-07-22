from django.db import models
from django.urls import reverse
from datetime import datetime
from django.db.models import CheckConstraint, Q, F
from django.utils import tree
from django.contrib.postgres.fields import ArrayField
from core.models import RequestResponse, BaseModel, Person,PersonRequest,Alerts
from correspondence.models import Radicate
from crum import get_current_user
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid

class Record(BaseModel):
    class Phases(models.TextChoices):
        GESTION = 'AG', _('Archivo de Gestión')
        CREATED = 'AC', _('Archivo Central')
        ASSIGNED = 'AI', _('Archivo Inactivo')
    class SecurityLevels(models.TextChoices):
        PUBLIC = 'PU', _('Público')
        PRIVATE = 'PR', _('Privado')
        DEPENDENCE = 'DE', _('Dependencia')
        USER = 'US', _('Usuario')

    name = models.TextField(max_length=30, null=False, db_index=True, default='Por asignar')
    initial_date = models.DateField(null=False, default=datetime.now)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT, default=False)
    status = models.CharField(max_length=2, choices=Phases.choices, default=Phases.GESTION)
    subject = models.CharField(max_length=256, null=True)
    source = models.CharField(max_length=256, null=True)
    observations = models.CharField(max_length=256, null=True)
    security_levels = models.CharField(max_length=2, choices=SecurityLevels.choices, default=SecurityLevels.PUBLIC)
    cmis_id = models.TextField(max_length=128, null=False, default='Por asignar')

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

    class Meta:
        verbose_name= 'Grupo de interes PQRSD'
        verbose_name_plural= 'Grupos de interes PQRSD'

class Type(models.Model):
    name = models.CharField(max_length=128,editable=False)
    description = models.CharField(blank=False, null=False, max_length=256,default='')
    asociated_icon = models.CharField(blank=False, null=False, max_length=50,default='')
    max_response_days = models.SmallIntegerField(blank=False, null=False, default=15)
    min_response_days = models.SmallIntegerField(blank=False, null=False, default=1)
    is_selectable = models.BooleanField(default=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo PQRSD'
        verbose_name_plural= 'Tipos PQRSD'

class SubType(models.Model):
    type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name='subtypes')
    description = models.CharField(blank=False, null=False, max_length=256,default='')
    name = models.CharField(max_length=128)
    max_response_days = models.SmallIntegerField(blank=False, null=False, default=15)
    min_response_days = models.SmallIntegerField(blank=False, null=False, default=1)
    alerts = models.ManyToManyField(Alerts, related_name="alerts_subtype",blank=True)
    def __str__(self):
        return self.type.name + ' / ' + self.name
    
    def save(self, *args, **kwargs):
        if(self.max_response_days <= self.type.max_response_days):
            super(SubType, self).save(*args, **kwargs)
        else:
            raise Exception("max_response_days should be lower or equal to type.max_response_days")
    class Meta:
        verbose_name= 'Sub tipo PQRSD'
        verbose_name_plural= 'Sub tipos PQRSD'
class PQRS(models.Model):
    class Status(models.TextChoices):
        EMAIL = 'EM', _('Importada')
        CREATED = 'CR', _('Recibida')
        ASSIGNED = 'AS', _('Asignada')
        RETURNED = 'RT', _('Devuelto')
        
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    pqr_type = models.ForeignKey(Type,on_delete=models.PROTECT,related_name='pqrs_object_type',null =True)
    principal_person = models.ForeignKey(Person, on_delete=models.PROTECT,related_name='pqrs_object_principal_person',null=True)
    multi_request_person = models.ManyToManyField(PersonRequest, related_name="multi_pqrs_request_person")
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.CREATED)

    def get_status_str(self):
        return self.Status(self.status).label
    class Meta:
        verbose_name= 'Objeto PQRSD'
        verbose_name_plural= 'Objetos PQRSD'
# Create your models here.
class PqrsContent(Radicate):
    response_mode = models.ForeignKey(RequestResponse, on_delete=models.PROTECT, related_name='pqrs_response_mode')
    interestGroup = models.ForeignKey(InterestGroup, on_delete=models.PROTECT, related_name='pqr_interest_group', null=True, blank= True)
    subtype = models.ForeignKey(SubType, on_delete=models.PROTECT, related_name='pqr_type', null=True)
    pqrsobject = models.ForeignKey(PQRS,related_name='pqr_type_object', on_delete=models.PROTECT,blank=True, null=True)
    agreement_personal_data = models.BooleanField()

    def get_absolute_url(self):
        return reverse('pqrs_detail', args=[self.id])

    def get_pqrs_type_subtype(self):
        return f"{self.pqrsobject.pqr_type.name if self.pqrsobject and self.pqrsobject.pqr_type  else ''} {self.subtype.name if self.subtype else ''}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # user = get_current_user()
        # if user is not None:
        #     if not self.pk:
        #         self.user_creation = user
        #     else:
        #         self.user_updated = user
        super(PqrsContent, self).save()
    class Meta:
        verbose_name= 'Contenido PQRSD'
        verbose_name_plural= 'Contenidos PQRSD'