from django.contrib import admin
from correspondence.models import Radicate, Raft, Subraft, Doctype, DocsRetention, Record, \
    RadicateTypes, ReceptionMode, ProcessType, SecurityLevel, FilePhases, FinalDisposition, \
    AlfrescoFile, PermissionRelationReport, PermissionRelationAssignation
from core.models import Person, PersonRequest, UserProfileInfo, DocumentTypes, PersonType
from django.contrib.auth.models import Permission


class PermissionRelationReportAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fieldset', {'fields': ['current_permission', 'destination_permission', 'is_current_area']}),
    ]
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "current_permission":
            kwargs["queryset"] = Permission.objects.filter(codename__startswith='report')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "destination_permission":
            kwargs["queryset"] = Permission.objects.filter(content_type_id=4)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class PermissionRelationAssignationAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fieldset', {'fields': ['current_permission', 'destination_permission', 'is_current_area']}),
    ]
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "current_permission":
            kwargs["queryset"] = Permission.objects.filter(codename__startswith='assign_')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "destination_permission":
            kwargs["queryset"] = Permission.objects.filter(codename__startswith='receive_')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# Register your models here.
admin.site.register(Raft)
admin.site.register(Subraft)
admin.site.register(Doctype)
admin.site.register(UserProfileInfo)
admin.site.register(Person)
admin.site.register(PersonRequest)
admin.site.register(DocsRetention)
admin.site.register(Record)
admin.site.register(DocumentTypes)
admin.site.register(RadicateTypes)
admin.site.register(ReceptionMode)
admin.site.register(ProcessType)
admin.site.register(SecurityLevel)
admin.site.register(FilePhases)
admin.site.register(FinalDisposition)
admin.site.register(PersonType)
admin.site.register(AlfrescoFile)
admin.site.register(PermissionRelationReport, PermissionRelationReportAdmin)
admin.site.register(PermissionRelationAssignation, PermissionRelationAssignationAdmin)

@admin.register(Radicate)
class RadicateAdmin(admin.ModelAdmin):
    list_display = ('number', 'date_radicated', 'subject')
    list_filter = ('type', 'reception_mode', 'person', 'creator')
    search_fields = ('subject', 'number')
    ordering = ('-date_radicated',)
    date_hierarchy = 'date_radicated'
    raw_id_fields = ('person', 'creator')
