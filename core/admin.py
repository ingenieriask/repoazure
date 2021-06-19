from django.contrib import admin
from core.models import Attorny, AttornyType, Atttorny_Person, LegalPerson, State, City, Office, Country, PreferencialPopulation, \
    Disability, BooleanSelection, EthnicGroup, ResponseMode, SystemParameter, \
    AppParameter, ConsecutiveFormat, FilingType, CalendarDay, CalendarDayType, Calendar,Alerts
from core.forms import ConsecutiveFormatForm, CalendarForm, CustomGroupAdminForm, CustomUserChangeForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin

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

class CustomGroupAdmin(admin.ModelAdmin):
    form = CustomGroupAdminForm
    search_fields = ('name',)
    ordering = ('name',)

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm

# Register your models here.
admin.site.register(Attorny)
admin.site.register(AttornyType)
admin.site.register(Atttorny_Person)
admin.site.register(Alerts)
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
admin.site.register(CalendarDay)
admin.site.register(CalendarDayType)
admin.site.register(LegalPerson)
admin.site.register(Calendar, CalendarAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
