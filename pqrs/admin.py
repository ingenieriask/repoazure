from django.contrib import admin
from pqrs.models import PQRS, Type, SubType, PqrsContent, Topic, InterestGroup

class TypeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fieldset', {'fields': ['name', 'description', 'asociated_icon', 'max_response_days', 'min_response_days']}),
    ]
    readonly_fields = ('name',)

class PQRSAadmin(admin.ModelAdmin):
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Type, TypeAdmin)
admin.site.register(SubType)
admin.site.register(PQRS, PQRSAadmin)
admin.site.register(PqrsContent)
admin.site.register(Topic)
admin.site.register(InterestGroup)

