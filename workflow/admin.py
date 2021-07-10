from django.contrib import admin
from workflow.forms import SignatureFlowForm
from workflow.models import SignatureFlow

class SignatureFlowAdminForm(admin.ModelAdmin):
    form = SignatureFlowForm

admin.site.register(SignatureFlow, SignatureFlowAdminForm)
