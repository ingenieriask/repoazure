from django.db import models
from django.contrib.auth.models import User

class SignatureFlow(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
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

    def __str__(self):
        return f'{self.type} {self.previous}'
