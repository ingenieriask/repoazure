from pqrs.models import PqrsContent
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field
from crispy_forms.utils import TEMPLATE_PACK
from core.forms import AbstractPersonForm,AbstractPersonRequestForm,AbstractPersonAttorny,AbstractLegalPersonForm
from django.utils.translation import gettext_lazy as _
from core.forms import CustomFileInput
from core.utils_db import get_json_system_parameter
from captcha.fields import CaptchaField

class AgreementModal(Field):
    template='pqrs/agreement_modal.html'
    extra_context = {}

    def __init__(self, *args, **kwargs):
        self.extra_context = kwargs.pop('extra_context', self.extra_context)
        super(AgreementModal, self).__init__(*args, **kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, extra_context=None, **kwargs):
        if self.extra_context:
            extra_context = extra_context.update(self.extra_context) if extra_context else self.extra_context
        return super(AgreementModal, self).render(form, form_style, context, template_pack, extra_context, **kwargs)

class PersonForm(AbstractPersonForm):
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])
        self.Meta.model.reverse_url = 'pqrs:multi_request'

class PersonFormUpdate(AbstractPersonForm):
    def __init__(self,pk=None, pqrs_type=None, *args, **kwargs):
        super(PersonFormUpdate, self).__init__(*args, **kwargs)
        self.fields['document_type'].disabled = True
        self.fields['document_number'].disabled = True
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])

class LegalPersonForm(AbstractLegalPersonForm):
    def __init__(self, *args, **kwargs):
        super(LegalPersonForm, self).__init__(*args, **kwargs)
        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])

class PersonAttorny(AbstractPersonAttorny):
    def __init__(self,pqrs_type=None,  *args, **kwargs):
        super(PersonAttorny, self).__init__(*args, **kwargs)
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
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")
    agreement_personal_data = forms.BooleanField(widget=forms.CheckboxInput, required=True, 
        label="Acepto el tratamiento de datos personales"
        )
    
    def clean(self):
        cleaned_data = super().clean()
        print('resultade de captcha', cleaned_data.get('captcha'), cleaned_data.get('captcha') is None)
        if (cleaned_data.get('captcha') is None):
            raise forms.ValidationError('Por favor valide el captcha')
        return cleaned_data

    class Meta:
        model = PqrsContent
        fields = ('subject', 'data', 'topic', 'interestGroup', 'captcha', 'agreement_personal_data')
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'topic': 'Tema',
                  'interestGroup': 'Grupo de interés'}

    def __init__(self, *args, **kwargs):
        super(PqrRadicateForm, self).__init__(*args, **kwargs)
        agreement_data = get_json_system_parameter('AGREEMENT_DATA')
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('topic', css_class='form-group col-md-6 mb-0'),
                Column('interestGroup', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('subject', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('data', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(CustomFileInput('uploaded_files'),css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(AgreementModal('agreement_personal_data', extra_context=agreement_data),css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('captcha', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            
            Submit('submit', 'Radicar')
        )

        