from django.core.exceptions import ValidationError
from django.db import models
from datetime import datetime
from django.urls import reverse
from django.conf import settings
from crum import get_current_user
from core.models import Office, BaseModel, UserProfileInfo, Person
from django.contrib.auth.models import User, Permission
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Raft(models.Model):
    description = models.TextField(max_length=64, null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.description


class Subraft(models.Model):
    raft = models.ForeignKey(Raft, on_delete=models.CASCADE, related_name='subseries')
    description = models.TextField(max_length=64, null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.raft.description + ' / ' + self.description


class Doctype(models.Model):
    sub_raft = models.ForeignKey(Subraft, on_delete=models.CASCADE, related_name='tipos_doc')
    description = models.TextField(max_length=64, null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.sub_raft.raft.description + ' / ' + self.sub_raft.description + ' / ' + self.description
    class Meta:
        verbose_name= 'Tipo de Documento'
        verbose_name_plural= 'Tipos de Documentos'

class RadicateTypes(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo Radicado'
        verbose_name_plural= 'Tipos Radicados'


class ReceptionMode(models.Model):
    abbr = models.CharField(unique=True, max_length=10)
    name = models.CharField(unique=True, max_length=64)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Modo de Recepcion'
        verbose_name_plural= 'Modos de Recepcion'


class Radicate(models.Model):
    class Classification(models.TextChoices):
        PQR = 'PQR', _('PQRSD')
        AMPLIATION_REQUEST = 'AR', _('Solicitud de ampliación')
        AMPLIATION_ANSWER = 'AA', _('Respuesta de solicitante')
        COMPLETE_ANSWER = 'CA', _('Respuesta final')

    number = models.TextField(max_length=30, null=False, db_index=True)
    subject = models.CharField(max_length=256, null=True)
    annexes = models.TextField(max_length=256, null=True)
    observation = models.TextField(max_length=400, null=True)
    type = models.ForeignKey(RadicateTypes, on_delete=models.CASCADE, related_name='radicate_type', null=False, blank=False)
    date_radicated = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='radicates_creator', blank=True, null=True)
    record = models.ForeignKey('Record', on_delete=models.CASCADE, related_name='radicates', blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='radicates_person', default=False)
    current_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='radicates_user', blank=True, null=True)
    last_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='radicates_last_user', blank=True, null=True)
    reception_mode = models.ForeignKey(ReceptionMode, on_delete=models.CASCADE, null=False, blank=False)
    use_parent_address = models.BooleanField(default=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='radicates_office', default='1')
    doctype = models.ForeignKey(Doctype, on_delete=models.CASCADE, related_name='radicates_doctype', blank=True, null=True)

    parent = models.ForeignKey('Radicate', on_delete=models.PROTECT, related_name='associated_radicates', null=True)
    classification = models.CharField(max_length=3, choices=Classification.choices, default=Classification.PQR)
    folder_id = models.TextField(max_length=100, null=False, default='')

    reported_people = models.ManyToManyField(User, blank=True)

    class Meta:
        ordering = ['date_radicated']

    def __str__(self):
        return str(self.number)

    def get_classification_str(self):
        return self.Classification(self.classification).label

    def get_absolute_url(self):
        return reverse('correspondence:detail_radicate', args=[str(self.id)])

class ProcessActionStep(BaseModel):
    date_execution = models.DateTimeField(default=datetime.now, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prac_user', blank=True, null=True)
    destination_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prac_dest_user', blank=True, null=True)
    destination_users = models.ManyToManyField(User, related_name='prac_dest_users', blank=True)
    observation = models.TextField(max_length=512, null=True)
    detail = models.TextField(max_length=256, null=True)
    action = models.TextField(max_length=32, null=True)
    radicate = models.ForeignKey(Radicate, on_delete=models.PROTECT, related_name='history')

    def save(self):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(ProcessActionStep, self).save()

class PermissionRelationAssignation(BaseModel):
    current_permission = models.ForeignKey(Permission, on_delete=models.PROTECT)
    destination_permission = models.ManyToManyField(Permission, blank=True, related_name="assination_relation_permission")
    is_current_area = models.BooleanField()
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(PermissionRelationAssignation, self).save()
    class Meta:
        verbose_name= 'Asignacion de Permisos por Reporte'
        verbose_name_plural= 'Asignaciones de Permisos por Reportes'

class PermissionRelationReport(BaseModel):
    current_permission = models.ForeignKey(Permission, on_delete=models.PROTECT)
    destination_permission = models.ManyToManyField(Permission, blank=True, related_name="report_relation_permission")
    is_current_area = models.BooleanField()
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(PermissionRelationReport, self).save()
    class Meta:
        verbose_name= 'Relacion de Permiso por Reporte'
        verbose_name_plural= 'Relaciones de Permisos por Reportes'

class AlfrescoFile(models.Model):
    cmis_id = models.TextField(max_length=128, null=True)
    name = models.CharField(max_length=256, null=True)
    extension = models.CharField(max_length=4, null=True)
    size = models.IntegerField(default=0)
    radicate = models.ForeignKey(Radicate, on_delete=models.PROTECT, related_name='files')
    
    def __str__(self):
        return self.cmis_id
    class Meta:
        verbose_name= 'Archivo de Alfresco'
        verbose_name_plural= 'Archivos de Alfresco'

class DocsRetention(models.Model):
    subraft = models.ForeignKey(Subraft, on_delete=models.PROTECT, related_name='retentions')
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name='retentions')
    central_file_years = models.IntegerField(default=False)
    gestion_file_years = models.IntegerField(default=False)

    def __str__(self):
        return self.subraft.description + ' - ' + self.office.name
    class Meta:
        verbose_name= 'Retencion de Documento'
        verbose_name_plural= 'Retenciones de Documentos'

class ProcessType(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo de Proceso'
        verbose_name_plural= 'Tipos de Procesos'


class SecurityLevel(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name= 'Nivel de Seguridad'
        verbose_name_plural= 'Niveles de Seguridad'


class FilePhases(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name= 'Fase de Archivo'
        verbose_name_plural= 'Fases de los Archivos'


class FinalDisposition(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name= 'Disposicion Final'
        verbose_name_plural= 'Disposiciones Finales'


class Record(BaseModel):
    retention = models.ForeignKey(DocsRetention, on_delete=models.PROTECT, related_name='records', default=False)
    responsable = models.ForeignKey(UserProfileInfo, on_delete=models.PROTECT, related_name='record_responsable', default=False)
    process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE, null=False, blank=False)
    phase = models.ForeignKey(FilePhases, on_delete=models.CASCADE, null=False, blank=False)
    final_disposition = models.ForeignKey(FinalDisposition, on_delete=models.CASCADE, null=False, blank=False)
    security_level = models.ForeignKey(SecurityLevel, on_delete=models.CASCADE, null=False, blank=False)
    is_tvd = models.BooleanField()

    cmis_id = models.TextField(max_length=128, null=True)

    name = models.CharField(max_length=256)
    subject = models.CharField(max_length=256)
    source = models.CharField(max_length=256)
    init_process_date = models.DateField(auto_now=False)
    init_date = models.DateField(auto_now=False)
    final_date = models.DateField(auto_now=False)
    creation_date = models.DateField(auto_now=True)

    def get_absolute_url(self):
        return reverse('correspondence:detail_record', args=[self.id])

    def __str__(self):
        return self.name

    def set_cmis_id(self, cmis_id):
        self.cmis_id = cmis_id
        self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(Record, self).save()
    class Meta:
        verbose_name= 'Registro'
        verbose_name_plural= 'Registros'

def template_directory_path(instance, filename):
    return 'templates/{0}/{1}'.format(instance.office.name, filename)


def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(u'Archivo no soportado')


class Template(BaseModel):
    office = models.ForeignKey(to=Office, on_delete=models.CASCADE, related_name='templates')
    name = models.TextField(max_length=64, null=False)
    file = models.FileField(upload_to=template_directory_path)
    description = models.TextField(max_length=256)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(Template, self).save()

    @staticmethod
    def get_absolute_url():
        return reverse('correspondence:template_list')
