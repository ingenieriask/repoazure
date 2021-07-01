from os import closerange
from re import sub
from django.forms import widgets
from core.models import DocumentTypes
from pqrs.models import PqrsContent, SubType
from correspondence.models import Radicate
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field
from crispy_forms.utils import TEMPLATE_PACK
from core.forms import AbstractPersonForm,AbstractPersonRequestForm,AbstractPersonAttorny,AbstractLegalPersonForm
from django.utils.translation import gettext_lazy as _
from core.forms import CustomFileInput
from core.utils_db import get_json_system_parameter
from captcha.fields import CaptchaField
from django.db.models import Q
from core.utils import get_field_value

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


class PqrsConsultantForm(forms.Form):
    num_rad = forms.CharField(label='Numero Radicado' )
    document_type_company = forms.ModelChoiceField(
        queryset=DocumentTypes.objects.all(),
        label='Tipo de documento'
    )
    doc_num = forms.CharField(label='Numero de Documento ')
    captcha = CaptchaField()

    def __init__(self, *args, **kwargs):
        super(PqrsConsultantForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('num_rad', css_class='form-group col-md-4 mb-0'),
                Column('document_type_company',
                       css_class='form-group col-md-4 mb-0'),
                Column('doc_num', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('captcha', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Consultar PQRDS')
        )


class PqrRadicateForm(forms.ModelForm):
    captcha = CaptchaField()
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")
    agreement_personal_data = forms.BooleanField(widget=forms.CheckboxInput, required=True, 
        label="Acepto el tratamiento de datos personales"
        )
    subtype_field = forms.ModelChoiceField(
                        queryset=SubType.objects.none(),
                        label='Tema'
                    )
    def clean(self):
        cleaned_data = super(PqrRadicateForm, self).clean()
        cleaned_data['subtype'] = SubType.objects.get(pk = self.data['subtype_field'])

        if 'subtype' in self.errors:
            del self._errors['subtype']

        cleaned_data = super(PqrRadicateForm, self).clean()
        if (cleaned_data.get('captcha') is None):
            raise forms.ValidationError('Por favor valide el captcha')
        
        return cleaned_data

    class Meta:
        model = PqrsContent
        fields = ('subject', 'data', 'interestGroup', 'captcha', 'agreement_personal_data', 'subtype')
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'interestGroup': 'Grupo de interés'}

    def __init__(self, typePqr, *args, **kwargs):
        super(PqrRadicateForm, self).__init__(*args, **kwargs)
        agreement_data = get_json_system_parameter('AGREEMENT_DATA')
        
        self.fields['subtype_field'].queryset = SubType.objects.filter(Q(type=typePqr))
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('subtype_field', css_class='form-group col-md-6 mb-0'),
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

        
class PqrsExtendRequestForm(forms.ModelForm):
    '''captcha = CaptchaField()
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")
    agreement_personal_data = forms.BooleanField(widget=forms.CheckboxInput, required=True, 
        label="Acepto el tratamiento de datos personales"
        )
    subtype_field = forms.ModelChoiceField(
                        queryset=SubType.objects.none(),
                        label='Tema'
                    )
    def clean(self):
        cleaned_data = super(PqrRadicateForm, self).clean()
        cleaned_data['subtype'] = SubType.objects.get(pk = self.data['subtype_field'])

        if 'subtype' in self.errors:
            del self._errors['subtype']

        cleaned_data = super(PqrRadicateForm, self).clean()
        if (cleaned_data.get('captcha') is None):
            raise forms.ValidationError('Por favor valide el captcha')
        
        return cleaned_data'''

    person_type = forms.CharField(max_length=32, disabled=True, label="Tipo de persona")
    document_type = forms.CharField(disabled=True, label="Tipo de documento")
    document_number = forms.CharField(max_length=25, disabled=True, label="Número de documento")
    expedition_date = forms.DateField(disabled=True, required=False, label="Fecha de expedición")
    name = forms.CharField(max_length=256, disabled=True, label="Nombes")
    lasts_name = forms.CharField(max_length=256, disabled=True, label="Apellidos")
    email = forms.CharField(disabled=True, label="Correo Electrónico")
    address = forms.CharField(disabled=True, label="Dirección de correspondencia")
    phone_number = forms.CharField(disabled=True, required=False, label="Teléfono / Celular")
    city = forms.ChoiceField(disabled=True, required=False, label="Departamento / Municipio")
    subject = forms.ChoiceField(disabled=True, required=False, label="Departamento / Municipio")
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")
    
    
    class Meta:
        model = Radicate
        fields = ('observation',)
        labels = {
            'observation' : 'Descripción de la solicitud de ampliación'
        }
        widgets = {
            'observation' : forms.Textarea()
        }

    def __init__(self, radicate, *args, **kwargs):
        super(PqrsExtendRequestForm, self).__init__(*args, **kwargs)
        
        self.fields['person_type'].widget = forms.TextInput(attrs={'value': radicate.person.person_type, 'class': 'w-75'})
        self.fields['document_type'].widget = forms.TextInput(attrs={'value': radicate.person.document_type, 'class': 'w-75'})
        self.fields['document_number'].widget = forms.TextInput(attrs={'value': radicate.person.document_number, 'class': 'w-75'})
        self.fields['expedition_date'].widget = forms.TextInput(attrs={'value': radicate.person.expedition_date, 'class': 'w-75'})
        self.fields['name'].widget = forms.TextInput(attrs={'value': radicate.person.name})
        self.fields['lasts_name'].widget = forms.TextInput(attrs={'value': radicate.person.lasts_name})
        self.fields['email'].widget = forms.TextInput(attrs={'value': radicate.person.email})
        self.fields['address'].widget = forms.TextInput(attrs={'value': radicate.person.address})
        self.fields['phone_number'].widget = forms.TextInput(attrs={'value': radicate.person.phone_number})
        self.fields['city'].widget = forms.Select(attrs={'value': 'city'})
        self.fields['subject'].widget = forms.TextInput(attrs={'required': False, 'value': 'Ampliación de solicitud - '+radicate.subject})
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('person_type', css_class='form-group col-md-2 mb-0'),
                Column('document_type', css_class='form-group col-md-3 mb-0'),
                Column('document_number', css_class='form-group col-md-3 mb-0'),
                Column('expedition_date', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('address', css_class='form-group col-md-4 mb-0'),
                Column('phone_number', css_class='form-group col-md-4 mb-0'),
                Column('city', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('subject', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('observation', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('uploaded_files', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            
            Submit('submit', 'Radicar')
        )