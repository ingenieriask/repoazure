from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from workflow.services import FlowService

class SignatureFlowWidget(forms.Widget):
    ''' '''

    template_name = 'workflow/signature_flow_admin.html'

    def get_context(self, name, value, attrs=None):

        graph = FlowService.to_json(value, FlowService.FlowType.SIGNATURE) if value else ''

        return {'widget': {
            'name': name,
            'value': value if value else '',
            'graph': graph
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class FilingFlowWidget(forms.Widget):
    ''' '''

    template_name = 'workflow/filing_flow_admin.html'

    def get_context(self, name, value, attrs=None):

        graph = FlowService.to_json(value) if value else ''

        return {'widget': {
            'name': name,
            'value': value if value else '',
            'graph': graph
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)







