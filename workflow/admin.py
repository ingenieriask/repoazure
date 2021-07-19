from django.contrib import admin
from workflow.forms import SignatureFlowAdminForm, FilingFlowAdminForm
from workflow.models import SignatureFlow, FilingFlow

class SignatureFlowAdmin(admin.ModelAdmin):
    form = SignatureFlowAdminForm

class RadicateFlowAdminForm(admin.ModelAdmin):
    form = FilingFlowAdminForm

admin.site.register(SignatureFlow, SignatureFlowAdmin)
admin.site.register(FilingFlow, RadicateFlowAdminForm)
