from django.contrib import admin
from pqrs.models import Type, SubType, PQR,PQRSInbound

admin.site.register(Type)
admin.site.register(SubType)
admin.site.register(PQR)
admin.site.register(PQRSInbound)