from os import closerange
from re import search, sub
from django.contrib.auth.models import User
from django.forms import widgets
from core.widgets import RichTextTinyWidget
from six import class_types
from core.models import DocumentTypes, City
from pqrs.models import InterestGroup, PqrsContent, SubType, Type,Record
from correspondence.models import Radicate
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, Button, HTML
from crispy_forms.utils import TEMPLATE_PACK
from core.forms import AbstractPersonForm,AbstractPersonRequestForm,AbstractPersonAttorny,AbstractLegalPersonForm
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from core.forms import CustomFileInput
from core.services import SystemParameterHelper
from captcha.fields import CaptchaField
from django.db.models import Q
from datetime import date, timedelta
from captcha.models import CaptchaStore
from django.template import loader

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

class LegalPersonFormUpdate(AbstractLegalPersonForm):
    def __init__(self, *args, **kwargs):
        super(LegalPersonFormUpdate, self).__init__(*args, **kwargs)
        self.fields['document_company_number'].disabled = True
        self.fields['document_type_company'].disabled = True
        self.fields['document_number'].disabled = True
        self.fields['document_type'].disabled = True
        self.fields['expedition_date'].disabled = True
        self.fields['verification_code'].disabled = True
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


    def clean(self):
        cleaned_data = super(PqrsConsultantForm, self).clean()
        if (cleaned_data.get('captcha') is None):
            raise forms.ValidationError('Por favor valide el captcha')
        return cleaned_data
        
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
    pqrs_creation_uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (M??ltiples archivos - Tama??o m??ximo = 10 MB)")
    agreement_personal_data = forms.BooleanField(widget=forms.CheckboxInput, required=True, 
        label="Acepto el tratamiento de datos personales"
        )
    subtype_field = forms.ModelChoiceField(
                        queryset=SubType.objects.none(),
                        label='Tema'
                    )
    
    def clean_captcha(self):
        value = [self.data['captcha_0'], self.data['captcha_1']]
        response, value[1] = (value[1] or "").strip().lower(), ""
        new_captcha = CaptchaStore(response=response, hashkey=value[0])
        new_captcha.save()
        return value
    
    def clean(self):
        
        cleaned_data = super(PqrRadicateForm, self).clean()
        cleaned_data['subtype'] = SubType.objects.get(pk = self.data['subtype_field'])

        if 'subtype' in self.errors:
            del self._errors['subtype']

        cleaned_data = super(PqrRadicateForm, self).clean()
        #if (cleaned_data.get('captcha') is None):
        #    raise forms.ValidationError('Por favor valide el captcha')
        
        return cleaned_data

    class Meta:
        model = PqrsContent
        fields = ('subject', 'data', 'interestGroup', 'captcha', 'agreement_personal_data', 'subtype')
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'interestGroup': 'Grupo de inter??s'}

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
                Column(CustomFileInput('pqrs_creation_uploaded_files'),css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(AgreementModal('agreement_personal_data', extra_context=agreement_data),css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('captcha', css_class='form-group col-md-4 mb-0'),
                Column(HTML('<span class="js-captcha-refresh"><i class="fas fa-sync fa-lg"></i></span>'), css_class='form-group col-md-1 mb-0 mt-5'),
                Column(HTML('<h3 id="validate_captcha_error" style="color: red; display: none;">Por favor valide el captcha</h3>'), css_class='col-md-6 mb-0 mt-5'),
                css_class='form-row'
            )
        )

        
class PqrsExtendRequestForm(forms.ModelForm):    

    CHOICES = [('FIRMA JURIDICA','FIRMA JURIDICA'),('USUARIO','USUARIO')]

    person_type = forms.CharField(required=False, max_length=32, label=mark_safe("<strong>Tipo de persona</strong>"),
                                  widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_type = forms.CharField(required=False, label=mark_safe("<strong>Tipo de documento</strong>"),
                                    widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_number = forms.CharField(required=False, max_length=25, label=mark_safe("<strong>N??mero de documento</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    expedition_date_last_digit = forms.CharField(required=False, label=mark_safe("<strong>Fecha de expedici??n</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    name_company_name = forms.CharField(required=False, max_length=120, widget = forms.TextInput(attrs={'readonly':True}))
    lasts_name_representative = forms.CharField(required=False, max_length=120, widget = forms.TextInput(attrs={'readonly':True}))
    email = forms.CharField(max_length=100, label=mark_safe("<strong>Correo Electr??nico<strong>"),
                            widget = forms.TextInput(attrs={'readonly':True}))
    address = forms.CharField(max_length=120, required=False, label=mark_safe("<strong>Direcci??n de correspondencia</strong>"),
                              widget = forms.TextInput(attrs={'readonly':True}))
    phone_number = forms.CharField(required=False, label=mark_safe("<strong>Tel??fono / Celular</strong>"),
                                   widget = forms.TextInput(attrs={'readonly':True}))
    city = forms.CharField(required=False, label=mark_safe("<strong>Municipio / Departamento<strong>"),
                           widget = forms.TextInput(attrs={'readonly':True}))
    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label=mark_safe("<span class='far fa-file-alt fa-3x' style='color: blue;'></span><strong>  Anexos, Documentos<strong>"))
    #sign_type = forms.ChoiceField(required=False, widget = forms.RadioSelect(choices=CHOICES, attrs={'class': 'form-check-inline list-unstyled mx-4'}))
    
    class Meta:
        model = Radicate
        fields = ('data', 'number', 'subject')
        labels = {
            'data' : 'Descripci??n de la solicitud de ampliaci??n',
            'number' : mark_safe('<strong>N??mero de radicaci??n</strong>' ),
            'subject' : mark_safe("<strong>Asunto<strong>")
        }
        widgets = {
            'data' : RichTextTinyWidget(),
            'number' : forms.TextInput(attrs={'style':'font-size:20px; font-weight: bold;', 'class':' text-center w-50', 'readonly':True}),
            'subject' : forms.TextInput(attrs={'readonly':True})
        }

    def __init__(self, radicate, *args, **kwargs):
 
        super(PqrsExtendRequestForm, self).__init__(*args, **kwargs)
        
        if radicate.person:
            if radicate.person.person_type.abbr == 'PJ':
                self.fields['name_company_name'].label = mark_safe('<strong>Raz??n Social</strong>')
                self.fields['lasts_name_representative'].label = mark_safe('<strong>Nombres y apellidos representante legal</strong>')
                self.fields['lasts_name_representative'].required = False
                self.fields['expedition_date_last_digit'].label = mark_safe('<strong>D??gito de verificaci??n</strong>')      
                
            elif radicate.person.person_type.abbr == 'PN':
                self.fields['name_company_name'].label = mark_safe('<strong>Nombres</strong>')
                self.fields['lasts_name_representative'].label = mark_safe('<strong>Apellidos</strong>')
                self.fields['expedition_date_last_digit'].label = mark_safe('<strong>Fecha de expedici??n</strong>')
        else:
            self.fields['name_company_name'].label = mark_safe('<strong>Nombres</strong>')

        self.helper = FormHelper(self)
        if radicate.person:
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
                    Column('data', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column(CustomFileInput('uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                    css_class='form-row'
                )
            )
        else:
            self.helper.layout = Layout(
                Row(
                    Column('name_company_name', css_class='form-group col-md-6 mb-0'),
                    Column('email', css_class='form-group col-md-6 mb-0'),
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
                    Column(CustomFileInput('uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                    css_class='form-row'
                )
            )

class RenderHTML(widgets.Textarea):
    template_name = 'core/output_html_widget.html'
    def get_context(self, name, value, attrs=None):
        return {'widget': {
        'name': name,
        'value': value,
    }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class RequestAnswerForm(forms.ModelForm):

    uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label=mark_safe("<span class='far fa-file-alt fa-3x' style='color: blue;'></span><strong>  Anexos, Documentos<strong>"))
    question = forms.CharField(required = False, max_length=20000, label=mark_safe('<strong>Informaci??n solicitada</strong>'),
                             widget = RenderHTML)
    class Meta:
        model = Radicate
        fields = ('data', 'number')
        labels = {
            'data' : '<strong>Respuesta</strong>',
            'number' : mark_safe('<h3><strong>Radicado</strong></h3>'),
        }
        widgets = {
            'data' : RichTextTinyWidget(),
            'number' : forms.TextInput(attrs={'style':'font-size:20px; font-weight: bold;', 'class': 'w-50', 'readonly':True}),
        }
        
    def __init__(self, *args, **kwargs):

        super(RequestAnswerForm, self).__init__(*args, **kwargs)
        
        self.fields['number'].required = False
        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('question', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('data', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(CustomFileInput('uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                css_class='form-row'
            )
        )
        

class PqrsAnswerForm(forms.ModelForm):    

    CHOICES = [('FIRMA JURIDICA','FIRMA JURIDICA'),('USUARIO','USUARIO')]

    person_type = forms.CharField(required=False,max_length=32, label=mark_safe("<strong>Tipo de persona</strong>"),
                                  widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_type = forms.CharField(required=False,label=mark_safe("<strong>Tipo de documento</strong>"),
                                    widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    document_number = forms.CharField(required=False,max_length=25, label=mark_safe("<strong>N??mero de documento</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    expedition_date_last_digit = forms.CharField(required=False,label=mark_safe("<strong>D??gito de verificaci??n</strong>"),
                                      widget = forms.TextInput(attrs={'class': 'w-75', 'readonly':True}))
    name_company_name = forms.CharField(required=False,max_length=120, label=mark_safe("<strong>Raz??n social</strong>"),
                                   widget = forms.TextInput(attrs={'readonly':True}))
    lasts_name_representative = forms.CharField(required=False,max_length=120, label=mark_safe("<strong>Representante legal</strong>"),
                                     widget = forms.TextInput(attrs={'readonly':True}))
    email = forms.CharField(required=False,max_length=120, label=mark_safe("<strong>Correo Electr??nico</strong>"))
    other_emails = forms.CharField(max_length=100, required=False, label=mark_safe("<strong>Otros correos destinatarios<strong>"))
    address = forms.CharField(required=False,max_length=120, label=mark_safe("<strong>Direcci??n de correspondencia</strong>"))
    phone_number = forms.CharField(required=False, 
                                   label=mark_safe("<strong>Tel??fono / Celular</strong>"))
    
    city = forms.ModelChoiceField(required=False, label=mark_safe("<strong>Municipio / Departamento<strong>"),
                                  queryset=City.objects.all())
    # data = forms.CharField(required = False, max_length=20000, label=mark_safe('<strong>Respuesta</strong>'),
    #                          widget = forms.Textarea())
    answer_uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label=mark_safe("<span class='far fa-file-alt fa-3x' style='color: blue;'></span><strong>  Anexos, Documentos<strong>"))
    edit_subject = forms.BooleanField(widget=forms.CheckboxInput(), label="", required=False)
    #sign_type = forms.ChoiceField(required=False, widget = forms.RadioSelect(choices=CHOICES, attrs={'class': 'form-check-inline list-unstyled mx-4'}))
    
    class Meta:
        model = Radicate
        fields = ('number', 'subject', 'data')
        labels = {
            'number' : mark_safe('<strong>N??mero de radicaci??n</strong>' ),
            'subject' : mark_safe("<strong>Asunto<strong>"),
            'data': mark_safe("<strong>Respuesta<strong>")
        }
        widgets = {
            'number' : forms.TextInput(attrs={'style':'font-size:20px; font-weight: bold;', 'class':' text-center w-50', 'readonly':True}),
            'subject' : forms.TextInput(attrs={'readonly': True}),
            'data': RichTextTinyWidget()
        }

    def __init__(self, radicate, *args, **kwargs):
 
        super(PqrsAnswerForm, self).__init__(*args, **kwargs)
        
        if radicate.person:
            if radicate.person.person_type.abbr == 'PJ':
                self.fields['name_company_name'].label = mark_safe('<strong>Raz??n Social</strong>')
                self.fields['lasts_name_representative'].label = mark_safe('<strong>Representante legal</strong>')
                self.fields['lasts_name_representative'].required = False
                self.fields['expedition_date_last_digit'].label = mark_safe('<strong>D??gito de verificaci??n</strong>')  
                self.fields['expedition_date_last_digit'].required = False    
                
            elif radicate.person.person_type.abbr == 'PN':
                self.fields['name_company_name'].label = mark_safe('<strong>Nombres</strong>')
                self.fields['lasts_name_representative'].label = mark_safe('<strong>Apellidos</strong>')
                self.fields['expedition_date_last_digit'].label = mark_safe('<strong>Fecha de expedici??n</strong>')
        else:
            self.fields['name_company_name'].label = mark_safe('<strong>Nombres</strong>')

        self.fields['subject'].required = False
        
        self.helper = FormHelper(self)
        
        if radicate.person:
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
                    Column('other_emails', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('address', css_class='form-group col-md-4 mb-0'),
                    Column('phone_number', css_class='form-group col-md-4 mb-0'),
                    Column('city', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('subject', css_class='form-group col-md-11 mb-0'),
                    Column('edit_subject', css_class='form-group col-md-1 mb-0 mt-4'),
                    css_class='form-row'
                ),
                Row(
                    Column('data', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column(CustomFileInput('answer_uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                    css_class='form-row'
                )
            )
        else:
            self.helper.layout = Layout(
                Row(
                    Column('name_company_name', css_class='form-group col-md-6 mb-0'),
                    Column('email', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('subject', css_class='form-group col-md-11 mb-0'),
                    Column('edit_subject', css_class='form-group col-md-1 mb-0 mt-4'),
                    css_class='form-row'
                ),
                Row(
                    Column('data', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column(CustomFileInput('answer_uploaded_files'), css_class='form-group offset-2 col-md-8 mb-0'),
                    css_class='form-row'
                )
            )


class RecordsForm(forms.ModelForm):
    date = forms.DateField(
        widget = forms.DateInput(
            format='%YYYY-%mm-%d', 
            attrs={'type': 'date',})
        )
    type = forms.ModelChoiceField(
                        queryset=Type.objects.all(),
                        label="Serie"
                    )
    subtype_field = forms.ModelChoiceField(
                        queryset=SubType.objects.all(),
                        label="Sub-Serie"
                    )
    responsable = forms.ModelChoiceField(
                        queryset=User.objects.all(),
                    )        
    class Meta:
        model = Record
        fields = (
             'status','subject',
            'source','observations','security_levels')
        labels = {
            'date':'Fecha Inicial',
            'responsable':'Responsable',
            'status':'Estado',
            'subject':'Asunto',
            'source':'Fuente',
            'observations':'Observaciones',
            'security_levels':'Seguridad'
        }
    def __init__(self, pk=None, *args, **kwargs):

        super(RecordsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        cancel_url = reverse('pqrs:detail_pqr', kwargs={'pk': pk})
        self.helper.layout = Layout(
            Div(
                Div(HTML('Aplicacion de la TRD del expediente'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('type', css_class='form-group col-md-6 mb-0'),
                        Column('subtype_field', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
            ), css_class="card mb-3",
            ), 
            Div(
                Div(HTML('Expediente'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('responsable', css_class='form-group col-md-6 mb-0'),
                        Column('date', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('security_levels', css_class='form-group col-md-6 mb-0'),
                        Column('status', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('subject', css_class='form-group col-md-4 mb-0'),
                        Column('source', css_class='form-group col-md-4 mb-0'),
                        Column('observations', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
            ), css_class="card mb-3",
            ),
            Div(
                Button('cancel', 'Volver', onclick='window.location.href="{}"'.format(
                    cancel_url), css_class='btn btn-primary'),
                Submit('submit','Siguiente',
                css_class="btn btn-success",
                )
                ,css_class="d-flex"
            )
            
        )

class ChangeClassificationForm(forms.Form):
    pqrs_type = forms.ModelChoiceField(
        queryset=Type.objects.filter(is_selectable=True),
        required=True,
        label='Tipo')
    pqrs_subtype = forms.ModelChoiceField(
        queryset=SubType.objects.all(),
        required=True,
        label='Tema')
    interest_group = forms.ModelChoiceField(
        queryset=InterestGroup.objects.all(),
        required=True,
        label='Grupo de Interes')
    
class SearchPqrsd(forms.Form):
    current_date = date.today().isoformat()   
    days_before = (date.today()-timedelta(days=30)).isoformat()
    days_after = (date.today()+timedelta(days=30)).isoformat()  
    key_word = forms.CharField(
        label='Palabra clave', 
        help_text='Datos a buscar',
        widget=forms.TextInput(
            attrs={'class':'textinput textInput form-control'})
        )
    since = forms.DateField(
        label=f"Desde (30 dias antes de hoy {current_date})",
        widget = forms.DateInput(
            format='%YYYY-%mm-%d', 
            attrs={
                'type': 'date',
                'value':str(days_before),
                'class':"dateinput form-control"
                })
        )
    until = forms.DateField(
        label=f"Hasta (30 dias despues de hoy {current_date})",
        widget = forms.DateInput(
            format='%YYYY-%mm-%d', 
            attrs={
                'type': 'date',
                'value':str(days_after),
                'class':"dateinput form-control"
                }))
    limit_finder = forms.CharField(
        max_length=20,
        widget = forms.HiddenInput(),
        initial="10",
        required=False)
    search_magic_word = forms.CharField(
        max_length=20,
        widget = forms.HiddenInput(),
        initial="None",
        required=False)