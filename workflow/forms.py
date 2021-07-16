from django import forms
import json
from workflow.models import SignatureFlow, RadicateFlow
from workflow.services import SignatureFlowService
from workflow.widgets import SignatureFlowWidget

class SignatureFlowForm(forms.ModelForm):

    class Meta:
        model = SignatureFlow
        fields = ['name', 'description']

class SignatureFlowAdminForm(forms.ModelForm):

    id = forms.CharField(max_length=50, required=False, widget=SignatureFlowWidget(), label='Graph')

    def clean(self, *args, **kwargs):

        cleaned_data = super(SignatureFlowAdminForm, self).clean()
        if self.data['id'] != -1:
            if self.data['graph'].strip():
                graph = json.loads(self.data['graph'])
                sf = SignatureFlowService.from_json(graph, self.cleaned_data['id'])

        return cleaned_data

    class Meta:
        model = SignatureFlow
        fields = ['name', 'description', 'id']

class RadicateFlowAdminForm(forms.ModelForm):

    id = forms.CharField(max_length=50, required=False, widget=SignatureFlowWidget(), label='Graph')

    def clean(self, *args, **kwargs):

        cleaned_data = super(RadicateFlowAdminForm, self).clean()
        if self.data['id'] != -1:
            if self.data['graph'].strip():
                graph = json.loads(self.data['graph'])
                sf = SignatureFlowService.from_json(graph, self.cleaned_data['id'])

        return cleaned_data

    class Meta:
        model = RadicateFlow
        fields = ['name', 'description', 'id']
