from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from datetime import date
from core.services import RecordCodeService, SystemParameterHelper
from core.models import CalendarDay

class ProceedingsConsecutiveFormatWidget(forms.Widget):
    '''Custom widget for the consecutive format definition'''

    template_name = 'core/consecutive_format_widget.html'

    def get_context(self, name, value, attrs=None):
        rino_parameter = SystemParameterHelper.get('CONFIRM_CONSECUTIVE_FORMAT')
        format, digits = RecordCodeService.decompile(value)
        return {'widget': {
            'name': name,
            'value': format,
            'digits': digits,
            'options': RecordCodeService.tokens['proceedings']
        },
        "message_confirm":rino_parameter.value}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class ConsecutiveFormatWidget(forms.Widget):
    '''Custom widget for the consecutive format definition'''

    template_name = 'core/consecutive_format_widget.html'

    def get_context(self, name, value, attrs=None):
        rino_parameter = SystemParameterHelper.get('CONFIRM_CONSECUTIVE_FORMAT')
        format, digits = RecordCodeService.decompile(value)
        return {'widget': {
            'name': name,
            'value': format,
            'digits': digits,
            'options': RecordCodeService.tokens['filing']
        },
        "message_confirm":rino_parameter.value}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class NonWorkingCalendarWidget(forms.Widget):
    '''Custom widget for non-working days configuration'''

    template_name = 'core/year_calendar_widget.html'

    def get_context(self, name, value, attrs=None):
        year = date.today().year
        return {'widget': {
            'name': name,
            'value': value,
            'year': year,
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class RichTextQuillWidget(forms.Widget):
    ''' '''

    #template_name = 'core/rich_text_widget.html'
    template_name = 'core/rich_text_quill_widget.html'

    def get_context(self, name, value, attrs=None):
        return {'widget': {
            'name': name,
            'value': value
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class RichTextTinyWidget(forms.Widget):
    ''' '''

    template_name = 'core/rich_text_tiny_widget.html'

    def get_context(self, name, value, attrs=None):
        return {'widget': {
            'name': name,
            'value': value
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)








