from django.contrib import admin
from core.models import State, City, Office, Country, PreferencialPopulation, Disability, BooleanSelection, EthnicGroup, ResponseMode, SystemParameter

# Register your models here.
admin.site.register(State)
admin.site.register(City)
admin.site.register(Country)
admin.site.register(Office)
admin.site.register(PreferencialPopulation)
admin.site.register(Disability)
admin.site.register(BooleanSelection)
admin.site.register(EthnicGroup)
admin.site.register(ResponseMode)
admin.site.register(SystemParameter)