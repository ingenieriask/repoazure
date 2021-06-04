from django.contrib import admin
from core.models import State, City, Office, Country, PreferencialPopulation, \
    Disability, BooleanSelection, EthnicGroup, ResponseMode, SystemParameter, \
    AppParameter, ConsecutiveFormat, FilingType, NonWorkingDay, NonWorkingDayType
from core.forms import ConsecutiveFormatForm, NonWorkingDayForm

class ConsecutiveFormatAdmin(admin.ModelAdmin):
    form = ConsecutiveFormatForm

class NonWorkingDayAdmin(admin.ModelAdmin):
    form = NonWorkingDayForm

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
admin.site.register(AppParameter)
admin.site.register(ConsecutiveFormat, ConsecutiveFormatAdmin)
admin.site.register(FilingType)
admin.site.register(NonWorkingDay)
admin.site.register(NonWorkingDayType)