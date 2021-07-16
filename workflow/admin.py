from django.contrib import admin
from workflow.forms import SignatureFlowForm, RadicateFlowAdminForm
from workflow.models import SignatureFlow, RadicateFlow

class SignatureFlowAdminForm(admin.ModelAdmin):
    form = SignatureFlowForm

class RadicateFlowAdminForm(admin.ModelAdmin):
    form = RadicateFlowAdminForm

admin.site.register(SignatureFlow, SignatureFlowAdminForm)
admin.site.register(RadicateFlow, RadicateFlowAdminForm)
