from django.core.exceptions import ValidationError
from django.db import models
from datetime import datetime
from django.urls import reverse
from django.conf import settings
from crum import get_current_user
from core.models import Office, BaseModel, UserProfileInfo, Person


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


class RadicateTypes(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class ReceptionMode(models.Model):
    abbr = models.CharField(unique=True, max_length=10)
    name = models.CharField(unique=True, max_length=64)

    def __str__(self):
        return self.name


class Radicate(models.Model):
    number = models.TextField(max_length=30, null=False, db_index=True)
    subject = models.TextField(max_length=256, null=True)
    annexes = models.TextField(max_length=256, null=True)
    observation = models.TextField(max_length=256, null=True)
    type = models.ForeignKey(RadicateTypes, on_delete=models.CASCADE, related_name='radicate_type', null=False, blank=False)
    date_radicated = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(UserProfileInfo, on_delete=models.CASCADE, related_name='radicates_creator', blank=True, null=True)
    record = models.ForeignKey('Record', on_delete=models.CASCADE, related_name='radicates', blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='radicates_person', default=False)
    current_user = models.ForeignKey(UserProfileInfo, on_delete=models.CASCADE, related_name='radicates_user', blank=True, null=True)
    reception_mode = models.ForeignKey(ReceptionMode, on_delete=models.CASCADE, null=False, blank=False)
    cmis_id = models.TextField(max_length=128, null=True)
    use_parent_address = models.BooleanField(default=False)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='radicates_office', default='1')
    doctype = models.ForeignKey(Doctype, on_delete=models.CASCADE, related_name='radicates_doctype', blank=True, null=True)

    class Meta:
        ordering = ['date_radicated']

    def __str__(self):
        return str(self.number)

    def get_absolute_url(self):
        return reverse('correspondence:detail_radicate', args=[str(self.id)])

    def set_cmis_id(self, cmis_id):
        self.cmis_id = cmis_id
        self.save()


class DocsRetention(models.Model):
    subraft = models.ForeignKey(Subraft, on_delete=models.PROTECT, related_name='retentions')
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name='retentions')
    central_file_years = models.IntegerField(default=False)
    gestion_file_years = models.IntegerField(default=False)

    def __str__(self):
        return self.subraft.description + ' - ' + self.office.name


class ProcessType(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class SecurityLevel(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class FilePhases(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class FinalDisposition(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Record(BaseModel):
    retention = models.ForeignKey(DocsRetention, on_delete=models.PROTECT, related_name='records', default=False)
    responsable = models.ForeignKey(UserProfileInfo, on_delete=models.PROTECT, related_name='record_responsable', default=False)
    # TODO manejar en tabla
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
