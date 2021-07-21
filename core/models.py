from django.db import models
from django.conf import settings
from django.http import response
from django.urls import reverse
from django.utils import timezone
from colorfield.fields import ColorField
from crum import get_current_user
from django.contrib.auth.models import User, Permission
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver
from treebeard.al_tree import AL_Node
from core.utils_services import FormatHelper
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from .utils_models import UploadToPathAndRename, OverwriteStorage

import os

# Create your models here.


class BaseModel(models.Model):
    user_creation = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='%(app_label)s_%(class)s_creation', null=True, blank=True)
    user_updated = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='%(app_label)s_%(class)s_update', null=True, blank=True)
    date_creation = models.DateTimeField(
        auto_now=False, auto_now_add=True, null=True, blank=True)
    date_updated = models.DateTimeField(
        auto_now=True, auto_now_add=False, null=True, blank=True)

    class Meta:
        abstract = True


# keyValue classes
class SystemParameter(models.Model):
    name = models.CharField(unique=True, max_length=128)
    value = models.TextField()

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Parametros del Sistema'
        
        
class SystemHelpParameter(models.Model):
    name = models.CharField(unique=True, max_length=128)
    value = models.TextField()

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Parametros de Ayudas del Sistema'


class PreferencialPopulation(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name= 'Poblacion Preferencial'


class Disability(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name= 'Dicapacidades'


class AttornyType(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo Apoderado'
        verbose_name_plural= 'Tipos de Apoderados'

class Alert(BaseModel):
    icon = models.CharField(max_length=128, default='activity')
    info = models.CharField(max_length=128)
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_user', blank=False, null=False)
    href = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    def save(self):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(Alert, self).save()

class BooleanSelection(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Opcione Booleana'
        verbose_name_plural= 'Opciones Booleanas'

class EthnicGroup(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name= 'Grupo Etnico'
        verbose_name_plural= 'Grupos Etnicos'

# Office attributes related to the person working Office
class Office(models.Model):
    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=10)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateField(auto_now=True)
    date_closed = models.DateTimeField(auto_now=False, null=True, blank=True)
    is_active = models.BooleanField()

    def __str__(self):
        return str(self.name) + ' - ' + str(self.abbr)

    class Meta:
        verbose_name= 'Oficina'
        verbose_name_plural= 'Oficinas'
class Country(models.Model):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=4)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Pais'
        verbose_name_plural= 'Paises'


class State(models.Model):
    country = models.ForeignKey(
        'Country', on_delete=models.CASCADE, related_name='states', default=False)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name= 'Estado o Departamento'
        verbose_name_plural= 'Estados o Departamentos'


class City(models.Model):
    name = models.CharField(max_length=128)
    state = models.ForeignKey(
        'State', on_delete=models.CASCADE, related_name='cities')
    city_id = models.IntegerField(default=False)

    class Meta:
        ordering = ['name']
        verbose_name= 'Ciudad'
        verbose_name_plural= 'Ciudades'

    def __str__(self):
        return self.name + ' / ' + self.state.name


class Alerts(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    response_time = models.SmallIntegerField(
        blank=False, null=False, default=1,verbose_name='Response Time (Days)')
    color = ColorField(default='#FF0000')
    history = HistoricalRecords()
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name= 'Alerta'
        verbose_name_plural= 'Alertas'
# UserProfileInfo, has one user for extend the basic user info


class UserProfileInfo(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile_user')
    office = models.ForeignKey(
        Office, on_delete=models.CASCADE, related_name='user_profiles', default=False)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name + ' (' + self.office.name + ') '
    class Meta:
        verbose_name= 'Informacion Perfil de Usuario'
        verbose_name_plural= 'Informacion Perfiles de Usuarios'

class PersonType(models.Model):
    abbr = models.CharField(max_length=2)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo Persona'
        verbose_name_plural= 'Tipos de Personas'


class DocumentTypes(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo de Documento'
        verbose_name_plural= 'Tipos de Documentos'

class RequestResponse(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo Respuesta Peticion'
        verbose_name_plural= 'Tipos Respuestas Peticiones'


class PersonBase(BaseModel):
    phone_number = models.CharField(blank=True, null=True, max_length=12)
    document_type = models.ForeignKey(DocumentTypes, on_delete=models.PROTECT, null=True, blank=True)
    person_type = models.ForeignKey(PersonType, related_name='personType', on_delete=models.PROTECT, null=True, blank=True, default=1)
    document_number = models.CharField(max_length=25, null=True, unique=True, db_index=True)
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    lasts_name = models.CharField(max_length=256,  null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='persons', null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True, unique=False)
    expedition_date = models.DateField(auto_now=False, null=True, blank=True)


class Attorny(PersonBase):
    professional_card = models.CharField(max_length=25, null=True, blank=True)

    def __str__(self):
        return f"{self.name} {self.lasts_name}"
    class Meta:
        verbose_name= 'Apoderado'
        verbose_name_plural= 'Apoderados'

class LegalPerson(PersonBase):
    verification_code = models.CharField(max_length=10, null=False, blank=False)
    company_name = models.CharField(max_length=256, null=False, blank=False)
    document_company_number = models.CharField(max_length=25, null=True, unique=True, db_index=True)
    representative = models.CharField(max_length=256, null=True, blank=True)
    document_type_company = models.ForeignKey(DocumentTypes, on_delete=models.PROTECT, null=True, blank=True, default=3)

    def __str__(self):
        return self.company_name

    def get_anonymized_email(self):
        return FormatHelper.anonymize(self.email)

    def get_anonymized_representative(self):
        return FormatHelper.anonymize(self.representative)
    
    class Meta:
        verbose_name= 'Persona Legal'
        verbose_name_plural= 'Personas Legales'


class Person(PersonBase):
    is_anonymous = models.BooleanField(blank=False, null=False, default=False)
    parent = models.ForeignKey(LegalPerson, on_delete=models.PROTECT, blank=True, null=True)
    preferencial_population = models.ManyToManyField(PreferencialPopulation, blank=True)
    conflict_victim = models.ForeignKey(BooleanSelection, on_delete=models.PROTECT, related_name='victimPerson', null=True, blank=True)
    disabilities = models.ManyToManyField(Disability, blank=True)
    ethnic_group = models.ForeignKey(EthnicGroup, on_delete=models.PROTECT, null=True, blank=True)
    attornyCheck = models.BooleanField(default=False, blank=True, null=True)
    request_response = models.ForeignKey(RequestResponse, on_delete=models.PROTECT, default=1)
    reverse_url = 'correspondence:detail_person'
    uuid = ''

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(self.reverse_url, args=[str(self.id)])

    def get_full_name(self):
        return f'{self.name} {self.lasts_name}'

    def get_anonymized_name(self):
        return FormatHelper.anonymize(self.name)

    def get_anonymized_email(self):
        return FormatHelper.anonymize(self.email)

    def get_anonymized_address(self):
        return FormatHelper.anonymize(self.address)

    def get_addresses(self):
        address_list = [(1, self.address)]
        if hasattr(self.parent, 'address'):
            address_list.append((2, self.parent.address))

        return address_list
    class Meta:
        verbose_name= 'Persona Natural'
        verbose_name_plural= 'Personas Naturales'

def get_first_name(self):
    return self.first_name + ' ' + self.last_name


User.add_to_class("__str__", get_first_name)


class PersonRequest(BaseModel):
    phone_number = models.CharField(blank=True, null=True, max_length=12)
    document_type = models.ForeignKey(
        DocumentTypes, on_delete=models.PROTECT, null=True, blank=True)
    person_type = models.ForeignKey(PersonType, related_name='personPeititionType',
                                    on_delete=models.PROTECT, null=True, blank=True, default=1)
    document_number = models.CharField(
        max_length=25, null=True, unique=True, db_index=True)
    expedition_date = models.DateField(auto_now=False)
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    lasts_name = models.CharField(max_length=256, null=False, blank=False)
    city = models.ForeignKey(City, on_delete=models.PROTECT,
                             related_name='personsCityPetition', null=True, blank=True)
    address = models.CharField(
        max_length=256, null=True, blank=True, unique=False)
    uuid = ''

    def __str__(self):
        return self.name

    class Meta:
        verbose_name= 'Persona adicional en la Peticion'
        verbose_name_plural= 'Personas adicionales en la Peticion'

def get_first_name(self):
    return self.first_name + ' ' + self.last_name


User.add_to_class("__str__", get_first_name)


class Atttorny_Person(models.Model):
    attorny = models.ForeignKey(
        Attorny, related_name="attorny_extends", on_delete=models.PROTECT)
    person = models.ForeignKey(
        Person, related_name="persons_extends", on_delete=models.PROTECT)
    attorny_type = models.ForeignKey(
        AttornyType, related_name='attorny_type', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.attorny.name}-{self.attorny_type.name}-{self.person.name}"
    class Meta:
        verbose_name= 'Relacion Apoderado Persona'
        verbose_name_plural= 'Relaciones Apoderados Personas'

class AppParameter(models.Model):
    name = models.CharField(unique=True, max_length=128)
    value = models.TextField()

    def __str__(self):
        return f"{self.name}:{self.value}"

    class Meta:
        db_table = "core_app_parameter"
        verbose_name= 'Parametro de la Aplicacion'
        verbose_name_plural= 'Parametros de la Aplicacion'

class ConsecutiveFormat(models.Model):
    format = models.CharField(max_length=256, null=False, blank=False)
    effective_date = models.DateTimeField(
        default=timezone.now, null=False, blank=False)
        
    history = HistoricalRecords()
    def __str__(self):
        return f"'{self.format}' {self.effective_date}"

    class Meta:
        db_table = "core_consecutive_format"
        verbose_name= 'Formato del Consecutivo'
        verbose_name_plural= 'Formatos de los Consecutivos'


class FilingType(models.Model):
    name = models.CharField(max_length=128, blank=False,
                            null=False, default='')
    description = models.CharField(
        blank=False, null=False, max_length=256, default='')
    asociated_icon = models.CharField(
        blank=False, null=False, max_length=50, default='')
    code = models.CharField(max_length=16, blank=False, null=False, default='')
    identifier = models.CharField(
        max_length=16, blank=False, null=False, default='')

    def __str__(self):
        return f"{self.name} {self.code}"
    class Meta:
        verbose_name= 'Tipo de Relleno'
        verbose_name_plural= 'Tipos de Rellenos'


class Consecutive(models.Model):
    current = models.BigIntegerField(null=False)
    date = models.DateTimeField(default=timezone.now, null=False, blank=False)
    type = models.ForeignKey(
        FilingType, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.current} {self.date} {self.type}"


class CalendarDayType(models.Model):
    name = models.CharField(max_length=128, blank=False,
                            null=False, default='')

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Tipo de Calendario por Dia'
        verbose_name_plural= 'Tipos de Calendarios por Dias'

class Calendar(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False, default='',
                            verbose_name='Calendar')

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Calendario'
        verbose_name_plural= 'Calendarios'

class CalendarDay(models.Model):
    date = models.DateField(default=timezone.now, null=False, blank=False)
    type = models.ForeignKey(
        CalendarDayType, on_delete=models.PROTECT, null=True, blank=True)
    calendar = models.ForeignKey(
        Calendar, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.date} {self.type}"
    
    class Meta:
        verbose_name= 'Dia por Calendario'
        verbose_name_plural= 'Dias por Calendarios'


class Holiday(models.Model):
    date = models.DateField(default=timezone.now, null=False, blank=False)
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, blank=True)
    local_name = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.date} {self.local_name}"


class FunctionalArea(AL_Node):
    parent = models.ForeignKey("self", related_name="children_set",
                               null=True, blank=True, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, blank=False,
                            null=False, default='')
    description = models.CharField(
        max_length=256, null=True, blank=True, default='')
    sib_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "core_functional_area"
        verbose_name= 'Area Funcional'
        verbose_name_plural= 'Areas Funcionales'

class FunctionalAreaUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    functional_area = models.ManyToManyField(FunctionalArea)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_functional_area_user(sender, instance, created, **kwargs):
    if created:
        FunctionalAreaUser.objects.create(user=instance)


class Menu(AL_Node):
    parent = models.ForeignKey("self", related_name="children_set",
                               null=True, blank=True, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, blank=False,
                            null=False, default='')
    description = models.CharField(
        max_length=256, null=True, blank=True, default='')
    url_name = models.CharField(
        max_length=256, null=True, blank=True, default='')
    sib_order = models.PositiveIntegerField()
    icon = models.CharField(max_length=128, null=True, blank=True, default='')
    required_permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Menu'
        verbose_name_plural= 'Menus'

class NotificationsService(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=256)
    

    def __str__(self):
        return self.name


class Notifications(models.Model):
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=256)
    body = models.TextField(blank=True, null=True)
    body_sms = models.TextField(blank=True, null=True)
    notifications_services = models.ManyToManyField(
        NotificationsService, blank=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name= 'Notificacion'
        verbose_name_plural= 'Notificaciones'

def template_directory_path(instance, filename):
    return 'templates/{0}/{1}'.format(instance.type, filename)

class Template(BaseModel):
    class Types(models.TextChoices):
        PQR_CREATION = 'CR', _('Documento de radicación')
        PQR_LABEL = 'LB', _('Etiqueta de radicación')
        PQR_ANSWER = 'AN', _('Documento de respuesta')

    type = models.CharField(unique=True, max_length=2, choices=Types.choices, default=Types.PQR_CREATION)
    file = models.FileField(upload_to=template_directory_path)
    name = models.TextField(max_length=64, null=False)
    description = models.TextField(max_length=256)

    def __str__(self):
        return self.name

    def save(self):
        user = get_current_user()
        if user is not None:
            if not self.pk:
                self.user_creation = user
            else:
                self.user_updated = user
        super(Template, self).save()

class StyleSettings(models.Model):
    primary = ColorField(default='#FFFF00')
    secondary = ColorField(default='#FFFF00')
    h1_size = models.FloatField(default=1.5)
    h2_size = models.FloatField(default=1.4)
    h3_size = models.FloatField(default=1.3)
    h4_size = models.FloatField(default=1.2)
    h5_size = models.FloatField(default=1.1)
    h16_size = models.FloatField(default=1)
    p_size = models.FloatField(default=1)
    logo = models.ImageField(upload_to=UploadToPathAndRename(os.path.join('company_logo')), null=True,
                            storage=OverwriteStorage())

    class Meta:
        verbose_name= 'Parametrización del Tema'
        verbose_name_plural= 'Parametrizaciones del Tema'
