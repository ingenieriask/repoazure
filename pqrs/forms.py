from os import closerange
from re import sub
from django.forms import widgets
from core.models import DocumentTypes
from pqrs.models import PqrsContent, SubType
from correspondence.models import Radicate
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, Button
from crispy_forms.utils import TEMPLATE_PACK
from core.forms import AbstractPersonForm,AbstractPersonRequestForm,AbstractPersonAttorny,AbstractLegalPersonForm
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from core.forms import CustomFileInput
from core.services import SystemParameterHelper
from captcha.fields import CaptchaField
from django.db.models import Q

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
    item = forms.CharField(label='Palabra clave (Numero de Documento, Nombre, Correo electronico )', help_text='Datos a buscar')


class SearchUniquePersonForm(forms.Form):
    doc_num = forms.CharField(label='Numero de Documento' )
    document_type= forms.ModelChoiceField(
        queryset=DocumentTypes.objects.all(),
        label='Tipo de documento'
    )
    def __init__(self, *args, **kwargs):
        super(SearchUniquePersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('doc_num',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ), Submit('submit', 'Buscar')
        )


class SearchLegalersonForm(forms.Form):
    doc_num = forms.CharField(label='Numero de Documento')
    document_type_company = forms.ModelChoiceField(
        queryset=DocumentTypes.objects.filter(
            Q(abbr='NIT') | Q(abbr="NIT-EX")),
        label='Tipo de documento'
    )
    verification_digit = forms.CharField(label='Codigo verificacion')

    def __init__(self, *args, **kwargs):
        super(SearchLegalersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('document_type_company',
                       css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column('doc_num',
                       css_class='form-group col-md-6 mb-0'),
                Column('verification_digit',
                       css_class='form-group col-md-6 mb-4'),
                css_class='form-row'
            ), Submit('submit', 'Buscar')
        )
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
        agreement_data = SystemParameterHelper.get_json('AGREEMENT_DATA')
        
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

    CHOICES = [('FIRMA JURIDICA','FIRMA JURIDICA'),('USUARIO','USUARIO')]

    person_type = forms.CharField(max_length=32, label=mark_safe("<strong>Tipo de persona</strong>"),
                                  widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_type = forms.CharField(label=mark_safe("<strong>Tipo de documento</strong>"),
                                    widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_number = forms.CharField(max_length=25, label=mark_safe("<strong>Número de documento</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    expedition_date_last_digit = forms.CharField(label=mark_safe("<strong>Fecha de expedición</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    name_company_name = forms.CharField(max_length=120, widget = forms.TextInput(attrs={'readonly':True}))
    lasts_name_representative = forms.CharField(max_length=120, widget = forms.TextInput(attrs={'readonly':True}))
    email = forms.CharField(max_length=100, label=mark_safe("<strong>Correo Electrónico<strong>"),
                            widget = forms.TextInput(attrs={'readonly':True}))
    address = forms.CharField(max_length=120, required=False, label=mark_safe("<strong>Dirección de correspondencia</strong>"),
                              widget = forms.TextInput(attrs={'readonly':True}))
    phone_number = forms.CharField(required=False, label=mark_safe("<strong>Teléfono / Celular</strong>"),
                                   widget = forms.TextInput(attrs={'readonly':True}))
    city = forms.CharField(required=False, label=mark_safe("<strong>Municipio / Departamento<strong>"),
                           widget = forms.TextInput(attrs={'readonly':True}))
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label=mark_safe("<span class='far fa-file-alt fa-3x' style='color: blue;'></span><strong>  Anexos, Documentos<strong>"))
    #sign_type = forms.ChoiceField(required=False, widget = forms.RadioSelect(choices=CHOICES, attrs={'class': 'form-check-inline list-unstyled mx-4'}))
    
    class Meta:
        model = Radicate
        fields = ('observation', 'number', 'subject')
        labels = {
            'observation' : 'Descripción de la solicitud de ampliación',
            'number' : mark_safe('<strong>Número de radicación</strong>' ),
            'subject' : mark_safe("<strong>Asunto<strong>")
        }
        widgets = {
            'observation' : forms.Textarea(),
            'number' : forms.TextInput(attrs={'style':'font-size:20px; font-weight: bold;', 'class':' text-center w-50', 'readonly':True}),
            'subject' : forms.TextInput(attrs={'readonly':True})
        }

    def __init__(self, radicate, *args, **kwargs):
 
        super(PqrsExtendRequestForm, self).__init__(*args, **kwargs)
        
        if radicate.person.person_type.abbr == 'PJ':
            self.fields['name_company_name'].label = mark_safe('<strong>Razón Social</strong>')
            self.fields['lasts_name_representative'].label = mark_safe('<strong>Nombres y apellidos representante legal</strong>')
            self.fields['lasts_name_representative'].required = False
            self.fields['expedition_date_last_digit'].label = mark_safe('<strong>Dígito de verificación</strong>')      
            
        elif radicate.person.person_type.abbr == 'PN':
            self.fields['name_company_name'].label = mark_safe('<strong>Nombres</strong>')
            self.fields['lasts_name_representative'].label = mark_safe('<strong>Apellidos</strong>')
            self.fields['expedition_date_last_digit'].label = mark_safe('<strong>Fecha de expedición</strong>')
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('person_type', css_class='form-group col-md-2 mb-0'),
                Column('document_type', css_class='form-group col-md-3 mb-0'),
                Column('document_number', css_class='form-group col-md-3 mb-0'),
                Column('expedition_date_last_digit', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name_company_name', css_class='form-group col-md-6 mb-0'),
                Column('lasts_name_representative', css_class='form-group col-md-6 mb-0'),
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
                Column(CustomFileInput('uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                css_class='form-row'
            )
        )
        

class RequestAnswerForm(forms.ModelForm):

    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label=mark_safe("<span class='far fa-file-alt fa-3x' style='color: blue;'></span><strong>  Anexos, Documentos<strong>"))
    
    class Meta:
        model = Radicate
        fields = ('observation', 'number')
        labels = {
            'observation' : '<strong>Descripción</strong>',
            'number' : mark_safe('<h3><strong>Radicado</strong></h3>'),
        }
        widgets = {
            'observation' : forms.Textarea(),
            'number' : forms.TextInput(attrs={'style':'font-size:20px; font-weight: bold;', 'class': 'w-50', 'readonly':True}),
        }
        
    def __init__(self, *args, **kwargs):

        super(RequestAnswerForm, self).__init__(*args, **kwargs)
        
        self.fields['number'].required = False
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('observation', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(CustomFileInput('uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                css_class='form-row'
            )
        )