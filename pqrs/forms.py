from pqrs.models import PqrsContent
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from core.forms import AbstractPersonForm,AbstractPersonRequestForm
from django.utils.translation import gettext_lazy as _

from captcha.fields import CaptchaField

class PersonForm(AbstractPersonForm):
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])
        # print(kwargs['instance'], self.Meta.model.uuid)
        # self.Meta.model.uuid = kwargs['uuid']
        # self.Meta.model.reverse_url = 'correspondence:detail_person'
        self.Meta.model.reverse_url = 'pqrs:multi_request'

class PersonFormUpdate(AbstractPersonForm):
    def __init__(self,pk=None, pqrs_type=None, *args, **kwargs):
        super(PersonFormUpdate, self).__init__(*args, **kwargs)
        self.fields['document_type'].disabled = True
        self.fields['document_number'].disabled = True
        self.fields['person_type'].disabled = True
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])

class PersonRequestForm(AbstractPersonRequestForm):
    def __init__(self,person=None, pqrs_type=None,*args, **kwargs):
        super(PersonRequestForm, self).__init__(*args, **kwargs)
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])

class PersonRequestFormUpdate(AbstractPersonRequestForm):
    def __init__(self,pk=None, pqrs_type=None, *args, **kwargs):
        super(PersonRequestFormUpdate, self).__init__(*args, **kwargs)
        self.fields['document_type'].disabled = True
        self.fields['document_number'].disabled = True
        self.fields['person_type'].disabled = True
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])
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
        model = PqrsContent
        fields = ('subject', 'data', 'response_mode', 'files_uploaded', 'captcha'
                )
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'files_uploaded': 'Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)',
                  'response_mode': 'Medio de respuesta'}
        
        widgets = {
            'files_uploaded' : forms.ClearableFileInput(attrs={'multiple': True}),
        }

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
                Column('files_uploaded', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('captcha', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Radicar')
        )

        