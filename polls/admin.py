from django.contrib import admin
from .models import AnswerOption, Question, Poll, PollInstance

# Register your models here.

admin.site.register(AnswerOption)
admin.site.register(Question)
admin.site.register(Poll)
admin.site.register(PollInstance)