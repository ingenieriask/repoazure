from django import forms
import json
from workflow.models import SignatureFlow, FilingFlow
from workflow.services import FlowService
from workflow.widgets import SignatureFlowWidget, FilingFlowWidget


class SignatureFlowAdminForm(forms.ModelForm):

    id = forms.CharField(max_length=50, required=False, widget=SignatureFlowWidget(), label='Graph')

    def clean(self, *args, **kwargs):

        cleaned_data = super(SignatureFlowAdminForm, self).clean()
        if self.data['id'] != -1:
            if self.data['graph'].strip():
                graph = json.loads(self.data['graph'])
                sf = FlowService.from_json(graph, FlowService.FlowType.SIGNATURE, self.cleaned_data['id'])

        return cleaned_data

    class Meta:
        model = SignatureFlow
        fields = ['name', 'description', 'id']

class FilingFlowAdminForm(forms.ModelForm):

    id = forms.CharField(max_length=50, required=False, widget=FilingFlowWidget(), label='Graph')

    def clean(self, *args, **kwargs):

        cleaned_data = super(FilingFlowAdminForm, self).clean()
        if self.data['id'] != -1:
            if self.data['graph'].strip():
                graph = json.loads(self.data['graph'])
                sf = FlowService.from_json(graph, None, self.cleaned_data['id'])

        return cleaned_data

    class Meta:
        model = FilingFlow
        fields = ['subtype', 'id']
