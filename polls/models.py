from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.

# Generic answer options model    
class AnswerOption(models.Model):
    number = models.PositiveIntegerField(default=0)
    description = models.CharField(blank=False, max_length=50, default='')
    
    def __str__(self):
        return f"{self.number} {self.description}"
    class Meta:
        verbose_name_plural= 'Opciones de Respuesta'
# Generic question model, has one set of answer options to extend the answer options model
class Question(models.Model):
    number = models.PositiveIntegerField(default=0)
    description = models.CharField(blank=False, max_length=256, default='')
    answer_options = models.ManyToManyField(AnswerOption)
    
    def __str__(self):
        return f"{self.description}"
    class Meta:
        verbose_name= 'Pregunta'


# Generic poll model, has several questions to extend several question models  
class Poll(models.Model):
    type_poll = models.PositiveIntegerField(primary_key=True)
    questions = models.ManyToManyField(Question)
    valid_since = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Poll type: {self.type_poll} {self.valid_since} {self.valid_until} "
    class Meta:
        verbose_name= 'Encuesta'
# Specific instance of a poll model, has one poll to extend from the generic poll model
class PollInstance(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    answers = ArrayField(models.PositiveIntegerField())
    
    def __str__(self):
        return f"Poll type: {self.poll.type_poll} {self.answers}"
    class Meta:
        verbose_name= 'Encuesta y Respuesta'
        verbose_name_plural= 'Encuestas y Respuestas'