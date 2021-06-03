from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User
from core.models import City, PreferencialPopulation
from core.forms import AbstractPersonForm
from correspondence.models import Radicate, UserProfileInfo, Record
from pqrs.models import PQR
from core.forms import CustomFileInput
from pinax.eventlog.models import log, Log
from django.urls import reverse
from crispy_forms.layout import Field, ButtonHolder, Button, Div, HTML
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from captcha.fields import CaptchaField

class PersonForm(AbstractPersonForm):
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper.layout.extend([Submit('submit', 'Siguiente')])
        # print(kwargs['instance'], self.Meta.model.uuid)
        # self.Meta.model.uuid = kwargs['uuid']
        # self.Meta.model.reverse_url = 'correspondence:detail_person'
        self.Meta.model.reverse_url = 'pqrs:pqrs_create'

class SearchPersonForm(forms.Form):
    item = forms.CharField(label='Palabra clave', help_text='Datos a buscar')

class PqrRadicateForm(forms.ModelForm):
    captcha = CaptchaField()

    def clean(self):
        cleaned_data = super().clean()
        print('resultade de captcha', cleaned_data.get('captcha'), cleaned_data.get('captcha') is None)
        if (cleaned_data.get('captcha') is None):
            raise forms.ValidationError('Por favor valide el captcha')
        return cleaned_data

    class Meta:
        model = PQR
        fields = ('subject', 'data', 'response_mode', 'captcha')
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'response_mode': 'Medio de respuesta'}


    def __init__(self, *args, **kwargs):
        super(PqrRadicateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('subject', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('data', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('response_mode', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('captcha', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Radicar')
        )
        