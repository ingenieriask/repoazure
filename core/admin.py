from django.contrib import admin,messages
from core.models import Attorny, AttornyType, Atttorny_Person, GenderTypes, LegalPerson, State, \
    City, Office, Country, PreferencialPopulation, Disability, BooleanSelection, \
    EthnicGroup, RequestResponse, SystemParameter, AppParameter, ConsecutiveFormat, \
    FilingType, CalendarDay, CalendarDayType, Calendar, Alerts, FunctionalArea, \
    FunctionalAreaUser, Menu, NotificationsService, Notifications, Template, \
    StyleSettings, Task, ProceedingsConsecutiveFormat
from core.forms import ConsecutiveFormatForm, CalendarForm, CustomGroupAdminForm, \
    CustomUserChangeForm, ProceedingsConsecutiveFormatForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin
from treebeard.admin import TreeAdmin
from simple_history.admin import SimpleHistoryAdmin    

class ProceedingsConsecutiveFormatAdmin(admin.ModelAdmin):
    form = ProceedingsConsecutiveFormatForm
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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


class FunctionalAreaInline(admin.StackedInline):
    model = FunctionalAreaUser
    can_delete = False
    verbose_name_plural = 'Functional Area'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):

    form = CustomUserChangeForm
    inlines = (FunctionalAreaInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


class FunctionalAreaAdmin(TreeAdmin):
    list_display = ('name', 'parent', 'description',)

class GeneralNullAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class TemplateAdmin(GeneralNullAdmin):
    exclude = ('type','name','description')

# Register your models here.
admin.site.register(Attorny)
admin.site.register(AttornyType)
admin.site.register(Atttorny_Person)
admin.site.register(Alerts,SimpleHistoryAdmin)
admin.site.register(State)
admin.site.register(City)
admin.site.register(Country)
admin.site.register(Office)
admin.site.register(PreferencialPopulation)
admin.site.register(Disability)
admin.site.register(BooleanSelection)
admin.site.register(EthnicGroup)
admin.site.register(RequestResponse)
admin.site.register(SystemParameter)
admin.site.register(Notifications)
admin.site.register(NotificationsService)
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
admin.site.register(FunctionalArea, FunctionalAreaAdmin)
admin.site.register(Menu)
admin.site.register(Template,TemplateAdmin)
admin.site.register(StyleSettings)
admin.site.register(GenderTypes)
admin.site.register(Task)
admin.site.register(ProceedingsConsecutiveFormat, ProceedingsConsecutiveFormatAdmin)


