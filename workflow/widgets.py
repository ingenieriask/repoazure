from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from workflow.services import SignatureFlowService

class SignatureFlowWidget(forms.Widget):
    ''' '''

    template_name = 'core/signature_flow.html'

    def get_context(self, name, value, attrs=None):

        graph = SignatureFlowService.to_json(value) if value else ''

        return {'widget': {
            'name': name,
            'value': value if value else '',
            'graph': graph
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class RadicateFlowWidget(forms.Widget):
    ''' '''

    template_name = 'workflow/radicate_flow.html'

    def get_context(self, name, value, attrs=None):

        graph = SignatureFlowService.to_json(value) if value else ''

        return {'widget': {
            'name': name,
            'value': value if value else '',
            'graph': graph
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)







