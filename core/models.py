from django.db import models
from django.conf import settings
from django.urls import reverse
from core.utils import anonymize
from django.utils import timezone

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class BaseModel(models.Model):
    user_creation = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='%(app_label)s_%(class)s_creation', null=True, blank=True)
    user_updated = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='%(app_label)s_%(class)s_update', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True, auto_now_add=False, null=True, blank=True)

    class Meta:
        abstract = True


# keyValue classes
class SystemParameter(models.Model):
    name = models.CharField(unique=True, max_length=128)
    value = models.TextField()

    def __str__(self):
        return self.name


class ResponseMode(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class PreferencialPopulation(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Disability(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class BooleanSelection(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class EthnicGroup(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


# Office attributes related to the person working Office
class Office(models.Model):
    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=10)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateField(auto_now=True)
    date_closed = models.DateTimeField(auto_now=False, null=True, blank=True)
    is_active = models.BooleanField()

    def __str__(self):
        return str(self.name) + ' - ' + str(self.abbr)


class Country(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='states', default=False)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=128)
    state = models.ForeignKey('State', on_delete=models.CASCADE, related_name='cities')
    city_id = models.IntegerField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name + ' / ' + self.state.name


# UserProfileInfo, has one user for extend the basic user info
class UserProfileInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_user')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='user_profiles', default=False)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name + ' (' + self.office.name + ') '


class PersonType(models.Model):
    abbr = models.CharField(max_length=2)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class DocumentTypes(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class RequestResponse(models.Model):
    abbr = models.CharField(max_length=10)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

# Generic person class, attributes for senders and receivers
class Person(BaseModel):
    is_anonymous = models.BooleanField(blank=False, null=False, default=False)
    phone_number = models.CharField(blank=True, null=True ,max_length=12)
    document_type = models.ForeignKey(DocumentTypes, on_delete=models.PROTECT, null=True, blank=True)
    request_response = models.ForeignKey(RequestResponse, on_delete=models.PROTECT, null=True, blank=True)
    person_type = models.ForeignKey(PersonType, related_name='personType',on_delete=models.PROTECT, null=True, blank=True)
    document_number = models.CharField(max_length=25, null=True, unique=True, db_index=True)
    expedition_date= models.DateField(auto_now=False)
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    lasts_name = models.CharField(max_length=256, null=False, blank=False)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='persons', null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True, unique=False)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
    preferencial_population = models.ManyToManyField(PreferencialPopulation, blank=True)
    conflict_victim = models.ForeignKey(BooleanSelection, on_delete=models.PROTECT, related_name='victimPerson', null=True, blank=True)
    disabilities = models.ManyToManyField(Disability, blank=True)
    ethnic_group = models.ForeignKey(EthnicGroup, on_delete=models.PROTECT, null=True, blank=True)
    reverse_url = 'correspondence:detail_person'
    uuid = ''

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(self.reverse_url, args=[str(self.id)])

    def get_anonymized_name(self):
        return anonymize(self.name)

    def get_anonymized_email(self):
        return anonymize(self.email)

    def get_anonymized_address(self):
        return anonymize(self.address)

    def get_addresses(self):
        address_list = [(1, self.address)]
        if hasattr(self.parent, 'address'):
            address_list.append((2, self.parent.address))

        return address_list


def get_first_name(self):
    return self.first_name + ' ' + self.last_name
    
User.add_to_class("__str__", get_first_name)

class AppParameter(models.Model):
    name = models.CharField(unique=True, max_length=128)
    value = models.TextField()

    def __str__(self):
        return f"{self.name}:{self.value}"

    class Meta:
        db_table = "core_app_parameter"

class ConsecutiveFormat(models.Model):
    format = models.CharField(max_length=256, null=False, blank=False)
    effective_date = models.DateTimeField(default=timezone.now, null=False, blank=False)

    def __str__(self):
        return f"'{self.format}' {self.effective_date}"

    class Meta:
        db_table = "core_consecutive_format"

class FilingType(models.Model):
    name = models.CharField(max_length=128,blank=False, null=False,default='')
    description = models.CharField(blank=False, null=False, max_length=256,default='')
    asociated_icon = models.CharField(blank=False, null=False, max_length=50,default='')
    code = models.IntegerField(blank=False, null=False,default=0)
    def __str__(self):
        return f"{self.name} {self.code}"

class Consecutive(models.Model):
    current = models.BigIntegerField(null=False)
    date = models.DateTimeField(default=timezone.now, null=False, blank=False)
    type = models.ForeignKey(FilingType, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.current} {self.date} {self.type}"
    

# Generic answer options model    
class AnswerOption(models.Model):
    number = models.PositiveIntegerField()
    description = models.CharField(blank=False, max_length=50, default='')
    
    def __str__(self):
        return f"{self.number} {self.description}"

# Generic question model, has one set of answer options to extend the answer options model
class Question(models.Model):
    description = models.CharField(blank=False, max_length=256, default='')
    answer_options = models.ManyToManyField(AnswerOption)
    
  
# Generic poll model, has several questions to extend several question models  
class Poll(models.Model):
    type_poll = models.PositiveIntegerField()
    questions = models.ManyToManyField(Question)
    valid_since = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

# Specific instance of a poll model, has one poll to extend from the generic poll model
class PollInstance(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    answers = ArrayField(models.PositiveIntegerField())
    