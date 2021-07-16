from django.db import models
from django.contrib.auth.models import User
from pqrs.models import SubType

class SignatureFlow(models.Model):
    name = models.CharField(max_length=128, null=True, blank=True, default='')
    description = models.CharField(max_length=256, null=True, blank=True, default='')

    def __str__(self):
        return self.name

class SignatureNode(models.Model):
    index = models.IntegerField(null=False)
    type = models.CharField(max_length=50)
    previous = models.ManyToManyField("self", symmetrical = False)
    properties = models.CharField(max_length=512)
    signature_flow = models.ForeignKey(SignatureFlow, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    time = models.IntegerField(null=False, default=2)

    def __str__(self):
        return f'{self.type} {self.previous}'

class RadicateFlow(models.Model):
    subtype = models.OneToOneField(SubType, on_delete=models.PROTECT, related_name='pqr_type', null=True)

    def __str__(self):
        return self.name

class RadicateNode(models.Model):
    index = models.IntegerField(null=False)
    type = models.CharField(max_length=50)
    previous = models.ManyToManyField("self", symmetrical = False)
    properties = models.CharField(max_length=512)
    radicate_flow = models.ForeignKey(RadicateFlow, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, symmetrical=False)
    time = models.IntegerField(null=False, default=2)

    def __str__(self):
        return f'{self.type} {self.previous}'
