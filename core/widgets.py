from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
import json
from core.services import RecordCodeService

class ConsecutiveFormatWidget(forms.Widget):
    '''Custom widget for the consecutive format definition'''

    template_name = 'core/consecutive_format_widget.html'

    def get_context(self, name, value, attrs=None):

        format, digits = RecordCodeService.decompile(value)

        return {'widget': {
            'name': name,
            'value': format,
            'digits': digits,
            'options': json.dumps(RecordCodeService.tokens),
            'colors': json.dumps(['bg-primary', 'bg-success', 'bg-warning'])
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class NonWorkingCalendarWidget(forms.Widget):
    '''Custom widget for non-working days configuration'''

    template_name = 'core/year_calendar_widget.html'

    def get_context(self, name, value, attrs=None):

        print(value)

        return {'widget': {
            'name': 'name',
            'value': 'value',
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)





