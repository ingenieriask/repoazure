from django.contrib import admin
from core.models import State, City, Office, Country, PreferencialPopulation, \
    Disability, BooleanSelection, EthnicGroup, ResponseMode, SystemParameter, \
    AppParameter, ConsecutiveFormat, FilingType, NonWorkingDay, NonWorkingDayType, \
    Calendar
from core.forms import ConsecutiveFormatForm, CalendarForm

class ConsecutiveFormatAdmin(admin.ModelAdmin):
    form = ConsecutiveFormatForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class CalendarAdmin(admin.ModelAdmin):
    form = CalendarForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
admin.site.register(Calendar, CalendarAdmin)