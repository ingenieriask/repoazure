from django.db import models
from django.contrib.auth.models import User
from pqrs.models import SubType
from django.utils.translation import gettext_lazy as _

class SignatureFlow(models.Model):
    name = models.CharField(max_length=128, null=True, blank=True, default='')
    description = models.CharField(max_length=256, null=True, blank=True, default='')

    def __str__(self):
        return self.name

class SignatureNode(models.Model):
    class Types(models.TextChoices):
        INPUT = 'Inicio', _('Inicio')
        OUTPUT = 'Fin', _('Fin')
        GUARANTORUSER = 'Visto Bueno', _('Visto Bueno')
        SIGNINGUSER = 'Firma Personal', _('Firma Personal')
        LEGALSIGNINGUSER = 'Firma Jurídica', _('Firma Jurídica')

    index = models.IntegerField(null=False)
    type = models.CharField(max_length=50)
    previous = models.ManyToManyField("self", symmetrical = False)
    properties = models.CharField(max_length=512)
    signature_flow = models.ForeignKey(SignatureFlow, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    time = models.IntegerField(null=False, default=2)

    def __str__(self):
        return f'{self.type} {self.previous}'

class FilingFlow(models.Model):
    subtype = models.OneToOneField(SubType, on_delete=models.PROTECT, null=False)

    def __str__(self):
        return f'{self.subtype.name}'

class FilingNode(models.Model):
    class Types(models.TextChoices):
        INPUT = 'Inicio', _('Inicio')
        OUTPUT = 'Fin', _('Fin')
        ASSIGNEDUSER = 'Asignar', _('Asignar')
        INFORMEDUSER = 'Notificar', _('Notificar')

    index = models.IntegerField(null=False)
    type = models.CharField(max_length=50)
    previous = models.ManyToManyField("self", symmetrical = False)
    properties = models.CharField(max_length=512)
    filing_flow = models.ForeignKey(FilingFlow, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, symmetrical=False)
    time = models.IntegerField(null=False, default=2)

    def __str__(self):
        return f'{self.type} {self.previous}'
