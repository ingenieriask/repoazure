from django.contrib import admin
from pqrs.models import Type, SubType, PQR,PQRSInbound

class TypeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fieldset', {'fields': ['name', 'description', 'asociated_icon', 'max_response_days', 'min_response_days']}),
    ]
    readonly_fields = ('name',)

admin.site.register(Type, TypeAdmin)
admin.site.register(SubType)
admin.site.register(PQR)
admin.site.register(PQRSInbound)
