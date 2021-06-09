from django.contrib import admin
from correspondence.models import Radicate, Raft, Subraft, Doctype, DocsRetention, Record, \
    RadicateTypes, ReceptionMode, ProcessType, SecurityLevel, FilePhases, FinalDisposition, Template
from core.models import Person, PersonRequest, UserProfileInfo, DocumentTypes, PersonType

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
admin.site.register(Template)

@admin.register(Radicate)
class RadicateAdmin(admin.ModelAdmin):
    list_display = ('number', 'date_radicated', 'subject')
    list_filter = ('type', 'reception_mode', 'person', 'creator')
    search_fields = ('subject', 'number')
    ordering = ('-date_radicated',)
    date_hierarchy = 'date_radicated'
    raw_id_fields = ('person', 'creator')
