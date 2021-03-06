from django.db.models.query_utils import Q
from core.services import SystemParameterHelper
from pqrs.models import PqrsContent, SubType
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, ButtonHolder, Button, Div, HTML
from django.contrib.auth.models import User
from correspondence.models import Radicate, Record, RequestInternalInfo
from core.models import DocumentTypes, FunctionalAreaUser, Person, UserProfileInfo
from core.forms import CustomFileInput
from core.utils_services import FormatHelper
from pinax.eventlog.models import log, Log
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.widgets import RichTextTinyWidget

from crispy_forms.bootstrap import (
    Accordion,
    AccordionGroup
)


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserProfileInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        exclude = ('user',)


class RadicateForm(forms.ModelForm):
    document_file = forms.FileField()

    class Meta:
        model = Radicate
        fields = ['use_parent_address', 'subject', 'annexes', 'observation', 'type', 'reception_mode',
                  'office', 'doctype']
        labels = {'use_parent_address': '¿Usar la dirección de la organización?', 'subject': 'Asunto',
                  'person': 'Remitente/Destinatario',
                  'annexes': 'Anexos', 'type': 'Tipo', 'reception_mode': 'Medio de recepción',
                  'observation': 'Observaciones', 'office': 'Dependencia',
                  'doctype': 'Tipo de documento'}
        widgets = {
            'type': forms.Select(attrs={'class': 'selectpicker'}),
            'reception_mode': forms.Select(attrs={'class': 'selectpicker'}),
            'subject': forms.TextInput(),
            'annexes': forms.TextInput(),
            'office': forms.Select(attrs={'class': 'selectpicker'}),
            'doctype': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7',
                                           'title': 'Seleccione..'})
        }

    def __init__(self, *args, **kwargs):
        super(RadicateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'use_parent_address',
            Row(
                Column('type', css_class='form-group col-md-6 mb-0'),
                Column('reception_mode', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'subject',
            'observation',
            'annexes',
            'office',
            'doctype',
            CustomFileInput('document_file'),
            Submit('submit', 'Radicar')
        )


class SearchForm(forms.Form):
    item = forms.CharField(label='Palabra clave', help_text='Datos a buscar')



class AssignToUserForm(forms.Form):
    observations = forms.CharField(label='Observaciones:', widget=forms.Textarea())
    
class RequestInternalInformatioForm(forms.Form):
    description = forms.CharField(label='DESCRIPCIÓN SOLICITUD DE INFORMACIÓN', widget=forms.Textarea())

class ReportToUserForm(forms.Form):
    observations = forms.CharField(label='Observaciones:', widget=forms.Textarea())

class DeleteFromReportedForm(forms.Form):
    observations = forms.CharField(label='Observaciones:', widget=forms.Textarea())

class ReturnToLastUserForm(forms.Form):
    observations = forms.CharField(label='Observaciones:', widget=forms.Textarea())


class SearchContentForm(forms.Form):
    term = forms.CharField(label='Búsqueda por términos clave',
                           help_text='Introduzca el termino a buscar')

class SearchUserForm(forms.Form):
    anonymous = forms.BooleanField(
        label='Solicictante Anonimo',
        widget= forms.CheckboxInput(),
        required=False)
    doc_num = forms.CharField(label='Numero de Documento' )
    document_type= forms.ModelChoiceField(
        queryset=DocumentTypes.objects.exclude(Q(id=3) | Q(id=6)),
        label='Tipo de documento'
    )
    def __init__(self, *args, **kwargs):
        super(SearchUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('anonymous', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-0'),
                Column('doc_num',
                       css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Submit('submit', 'Buscar'), css_class='d-flex justify-content-center',
            )
        )

class SearchLegalUserForm(forms.Form):
    doc_num = forms.CharField(label='Numero de Documento' )
    verification_code = forms.CharField(label='Codigo de Verificación' )
    document_type= forms.ModelChoiceField(
        queryset=DocumentTypes.objects.filter(Q(id=3) | Q(id=6)),
        label='Tipo de documento'
    )
    def __init__(self, *args, **kwargs):
        super(SearchLegalUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-4 mb-0'),
                Column('doc_num',
                       css_class='form-group col-md-4 mb-0'),
                Column('verification_code',
                       css_class='form-group col-md-4 mb-0'),
            ),
            Row(
                Submit('submit', 'Buscar'), css_class='d-flex justify-content-center',
            )
        )


class CorrespondenceRadicateForm(forms.ModelForm):
    pqrs_creation_uploaded_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")

    class Meta:
        model = PqrsContent
        fields = ('subject', 'data', 'interestGroup', 'subtype')
        labels = {'subject': 'Asunto',
                  'data': 'Detalle de la solicitud',
                  'interestGroup': 'Grupo de interés'}

    def __init__(self, *args, **kwargs):
        
        super(CorrespondenceRadicateForm, self).__init__(*args, **kwargs)        
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('subtype', css_class='form-group col-md-6 mb-0'),
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
        )

        self.helper.layout.extend([
            Div(
                Submit('submit','Siguiente',
                css_class="btn btn-primary mx-auto",
                ),css_class="d-flex"),
                ])
        self.fields['subtype'].widget = forms.HiddenInput()
        self.fields['interestGroup'].widget = forms.HiddenInput()
        
class PersonForm(forms.ModelForm):
    email_confirmation = forms.CharField(
        label='Confirmación del correo electrónico', required=True)

    def clean_email_confirmation(self):
        cd = self.cleaned_data
        if FormatHelper.get_field_value(cd, 'email_confirmation') != FormatHelper.get_field_value(cd, 'email'):
            raise forms.ValidationError(
                'El correo de validación no coincide con el correo')
        return FormatHelper.get_field_value(cd, 'email_confirmation')

    def clean(self):
        cleaned_data = super().clean()
        cleaned_address = cleaned_data.get('address')
        cleaned_email = cleaned_data.get('email')
        if cleaned_address is None and cleaned_email is None:
            raise forms.ValidationError(
                'Por favor ingrese la dirección de contacto o el correo electrónico')
        return cleaned_data

    class Meta:
        model = Person

        fields = ['document_type', 'document_number', 'name', 'email', 'city', 'address',
                  'parent', 'preferencial_population', 'conflict_victim', 'disabilities', 'ethnic_group']
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'name': 'Nombres', 'email': 'Correo electrónico',
                  'city': 'Ciudad / Municipio', 'address': 'Dirección de contacto',
                  'parent': 'Entidad',
                  'preferencial_population': 'Población Preferencial (Selección Múltiple)',
                  'conflict_victim': 'Población víctima del conflicto armado',
                  'disabilities': 'Población en situación de discapacidad (Selección Múltiple)',
                  'ethnic_group': 'Grupo Étnico'}

        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'parent': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'preferencial_population': forms.SelectMultiple(attrs={'class': 'selectpicker show-tick', 'data-size': '7'}),
            'conflict_victim': forms.Select(attrs={'class': 'selectpicker', 'data-size': '7'}),
            'disabilities': forms.SelectMultiple(attrs={'class': 'selectpicker', 'data-size': '7'}),
            'ethnic_group': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
        }

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Datos básicos'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('document_type',
                               css_class='form-group col-md-6 mb-0'),
                        Column('document_number',
                               css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('name', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Datos de contacto'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation',
                               css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-6 mb-0'),
                        Column('address', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(Div(HTML('Población Especial'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('preferencial_population',
                               css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('conflict_victim',
                               css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('disabilities',
                               css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('ethnic_group',
                               css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
            ),
                css_class="card mb-3",
            ),
            Submit('submit', 'Guardar')
        )


class ChangeCurrentUserForm(forms.ModelForm):
    class Meta:
        model = Radicate
        fields = ['current_user']
        labels = {'current_user': 'Usuario'}
        widgets = {
            'current_user': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'})
        }

    def save(self, commit=True):
        radicate = super(ChangeCurrentUserForm, self).save(commit=False)
        log(
            user=radicate.current_user.user,
            action="RADICATE_CHANGE_USER",
            obj=radicate,
            extra=dict(number=radicate.number,
                       message="Se ha re-asignado el usuario actual")
        )

        if commit:
            radicate.save()
        return radicate


class ChangeRecordAssignedForm(forms.ModelForm):
    class Meta:
        model = Radicate
        fields = ['record']
        labels = {'record': 'Expediente'}
        widgets = {
            'record': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'})
        }


class RecordForm(forms.ModelForm):
    class Meta:
        model = Record

        fields = ['retention', 'responsable', 'process_type', 'phase', 'final_disposition', 'security_level', 'is_tvd',
                  'name', 'subject', 'source', 'init_process_date', 'init_date', 'final_date']
        labels = {'retention': 'Tipificación',
                  'responsable': 'Usuario Responsable del Proceso',
                  'process_type': 'Proceso', 'phase': 'Fase',
                  'final_disposition': 'Disposición final', 'security_level': 'Nivel de seguridad',
                  'is_tvd': '¿Es Tabla de Valoración Documental?', 'name': 'Nombre', 'subject': 'Asunto',
                  'source': 'Fuente', 'init_process_date': 'Fecha inicial del proceso',
                  'init_date': 'Fecha inicial', 'final_date': 'Fecha final'}

        widgets = {
            'retention': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'responsable': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'init_process_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'init_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'final_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            )
        }

    # def save(self, commit=True):
    #     record = super(RecordForm, self).save(commit=False)
    #     # log(
    #     #     user='',
    #     #     action="RECORD_SAVE",
    #     #     obj=record,
    #     #     extra=dict(number=radicate.number, message="Se ha guardado el expediente")
    #     # )

    #     if commit:
    #         record.save()
    #     return record

    def __init__(self, *args, **kwargs):
        super(RecordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        cancel_url = reverse('correspondence:list_records')
        self.helper.layout = Layout(
            Row(
                Column('is_tvd', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('retention', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('subject', css_class='form-group col-md-6 mb-0'),
                Column('source', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('process_type', css_class='form-group col-md-6 mb-0'),
                Column('responsable', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('init_process_date',
                       css_class='form-group col-md-4 mb-0'),
                Column('init_date', css_class='form-group col-md-4 mb-0'),
                Column('final_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('phase', css_class='form-group col-md-4 mb-0'),
                Column('final_disposition',
                       css_class='form-group col-md-4 mb-0'),
                Column('security_level', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Guardar', css_class='btn btn-success'),
                Button('cancel', 'Volver', onclick='window.location.href="{}"'.format(
                    cancel_url), css_class='btn btn-primary')
            )
        )


class AnswerRequestForm(forms.ModelForm):
    request_answer_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False,
                                    label="Anexos, Documentos (Múltiples archivos - Tamaño máximo = 10 MB)")
    
    class Meta:
        model = RequestInternalInfo

        fields = ['answer']
        labels = {'answer': 'Respuesta'}

        widgets = {
            'answer': RichTextTinyWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(AnswerRequestForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('description', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(CustomFileInput('request_answer_file'),css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
        )