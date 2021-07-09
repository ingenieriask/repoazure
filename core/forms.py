from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, ButtonHolder, Button, Div, HTML
from django.db.models import query
from core.models import Attorny, AttornyType, DocumentTypes, LegalPerson, Person, \
    Disability, PreferencialPopulation, Disability, PersonRequest, PreferencialPopulation, \
    SignatureFlow
from crispy_forms.layout import Field
import json
from core.widgets import ConsecutiveFormatWidget, NonWorkingCalendarWidget, SignatureFlowWidget
from core.services import RecordCodeService, CalendarService, SignatureFlowService
from core.utils_services import FormatHelper
from django.db.models import Q
from django.contrib.auth.models import Permission, Group
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm


class CustomFileInput(Field):
    template = 'core/custom_fileinput.html'


class AbstractPersonForm(forms.ModelForm):
    email_confirmation = forms.CharField(
        label='Confirmación del correo electrónico', required=True)
    preferencial_population = forms.ModelMultipleChoiceField(
        queryset=PreferencialPopulation.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Población Preferencial (Selección Múltiple)')
    disabilities = forms.ModelMultipleChoiceField(
        queryset=Disability.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Población en situación de discapacidad (Selección Múltiple)')

    def clean_email_confirmation(self):
        cd = self.cleaned_data
        if (FormatHelper.get_field_value(cd, 'email_confirmation') != FormatHelper.get_field_value(cd, 'email')):
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

        fields = ['document_type', 'document_number', 'phone_number',
                  'request_response', 'expedition_date', 'name',
                  'lasts_name', 'email', 'city', 'address', 'parent', 'preferencial_population',
                  'conflict_victim', 'disabilities', 'ethnic_group', 'attornyCheck']
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'expedition_date': 'Fecha de expedición',
                  'request_response': '¿Por cual medio desea recibir su respuesta?',
                  'name': 'Nombres',
                  'phone_number': 'Telefóno/Célular',
                  'lasts_name': 'Apellidos',
                  'email': 'Correo electrónico',
                  'city': 'Ciudad / Municipio', 'address': 'Dirección de contacto',
                  'parent': 'Entidad',
                  'conflict_victim': 'Población víctima del conflicto armado',
                  'ethnic_group': 'Grupo Étnico',
                  'attornyCheck': "¿Presentará su solicitud con el acompañamiento de un apoderado?"}

        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'request_response': forms.Select(attrs={'class': 'selectpicker'}),
            'expedition_date': forms.DateInput(format='%Y-%m-%d', attrs={'placeholder': 'digite la fecha', 'type': 'date'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'parent': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'conflict_victim': forms.Select(attrs={'class': 'selectpicker', 'data-size': '7'}),
            'ethnic_group': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'attornyCheck': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super(AbstractPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Apoderado'),
                    css_class='card-header'),
                Div(

                    Row(
                        Column('attornyCheck', css_class='form-group col-md-12 mb-0'), css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información General'),
                    css_class='card-header'),
                Div(

                    Row(
                        Column('document_type',
                               css_class='form-group col-md-4 mb-0'),
                        Column('document_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('expedition_date',
                               css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('name', css_class='form-group col-md-6 mb-0'),
                        Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información de contacto'),
                    css_class='card-header'),
                Div(
                    Row(Column('request_response',
                        css_class='form-group col-md-6 mb-0'),),
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation',
                               css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-4 mb-0'),
                        Column('phone_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('address', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(Div(HTML('Población Especial'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('conflict_victim',
                               css_class='form-group col-md-6 mb-0'),
                        Column('ethnic_group',
                               css_class='form-group col-md-6 mb-0'),

                        css_class='form-row'
                    ),
                    Row(
                        Column('preferencial_population',
                               css_class='form-group col-md-6 mt-2'),
                        Column('disabilities',
                               css_class='form-group col-md-6 mt-2'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
            ),

                css_class="card mb-3",
            ),
        )


class AbstractPersonRequestForm(forms.ModelForm):
    class Meta:
        model = PersonRequest

        fields = ['document_type', 'document_number', 'phone_number',
                  'expedition_date', 'name',
                  'lasts_name', 'email', 'city', 'address', ]
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'expedition_date': 'Fecha de expedición',
                  'name': 'Nombres',
                  'phone_number': 'Telefóno/Célular',
                  'lasts_name': 'Apellidos',
                  'email': 'Correo electrónico',
                  'city': 'Ciudad / Municipio', 'address': 'Dirección de contacto', }

        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'expedition_date': forms.DateInput(format='%Y-%m-%d', attrs={'placeholder': 'digite la fecha', 'type': 'date'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
        }

    def __init__(self, *args, **kwargs):
        super(AbstractPersonRequestForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Información General'),
                    css_class='card-header'),
                Div(

                    Row(
                        Column('document_type',
                               css_class='form-group col-md-4 mb-0'),
                        Column('document_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('expedition_date',
                               css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('name', css_class='form-group col-md-6 mb-0'),
                        Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información de contacto'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('address', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-6 mb-0'),
                        Column('phone_number',
                               css_class='form-group col-md-6 mb-0'),

                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
        )


class AbstractLegalPersonForm(forms.ModelForm):
    document_type_company = forms.ModelChoiceField(
        queryset=DocumentTypes.objects.filter(
            Q(abbr='NIT') | Q(abbr="NIT-EX")),
        label='Tipo de identificación'
    )
    email_confirmation = forms.CharField(
        label='Confirmación del correo electrónico', required=True)

    def clean_email_confirmation(self):
        cd = self.cleaned_data
        if (FormatHelper.get_field_value(cd, 'email_confirmation') != FormatHelper.get_field_value(cd, 'email')):
            raise forms.ValidationError(
                'El correo de validación no coincide con el correo')
        return FormatHelper.get_field_value(cd, 'email_confirmation')

    class Meta:
        model = LegalPerson
        fields = [
            'document_number', 'document_company_number', 'verification_code',
            'phone_number', 'document_type',
            'expedition_date', 'company_name', 'name', 'lasts_name',
            'email', 'city', 'address']
        labels = {
            'verification_code': 'Código de verificación',
            'company_name': 'Razon Social',
            'document_number': 'Numero de documento',
            'document_company_number': 'Número de documento',
            'expedition_date': 'Fecha de expedición',
            'phone_number': 'Telefóno/Célular',
            'email': 'Correo electrónico',
            'city': 'Ciudad / Municipio', 'address': 'Dirección de contacto',
            'name': 'Nombres',
            'lasts_name': 'Apellidos',
            'document_type':'Tipo de documento' }

        widgets = {
            'expedition_date': forms.DateInput(format='%Y-%m-%d', attrs={'placeholder': 'digite la fecha', 'type': 'date'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'document_number':forms.NumberInput(attrs={'size': '14'}),
            'document_company_number':forms.NumberInput(attrs={'size': '14'}),
            'verification_code':forms.NumberInput(attrs={'size': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super(AbstractLegalPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Persona Jurídica'),
                    css_class='card-header'),
                Div(

                    Row(
                        Column('document_type_company',
                               css_class='form-group col-md-4 mb-0'),
                        Column('document_company_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('verification_code',
                               css_class='form-group col-md-4 mb-0'),
                        Column('company_name',
                               css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información de contacto Representante legal'),
                    css_class='card-header'),
                Div(
                    
                    Row(
                        Column('document_type',
                               css_class='form-group col-md-4 mb-0'),
                        Column('document_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('expedition_date',
                               css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ), Row(
                        Column('name', css_class='form-group col-md-6 mb-0'),
                        Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información de contacto'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation',
                               css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-4 mb-0'),
                        Column('phone_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('address', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            ),
        )


class AbstractPersonAttorny(forms.ModelForm):
    attorny_type = forms.ModelChoiceField(
        queryset=AttornyType.objects.all(),
        required=True,
        label='Tipo apoderado')
    email_confirmation = forms.CharField(
        label='Confirmación del correo electrónico', required=True)

    def clean_email_confirmation(self):
        cd = self.cleaned_data
        if (FormatHelper.get_field_value(cd, 'email_confirmation') != FormatHelper.get_field_value(cd, 'email')):
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
        model = Attorny

        fields = ['document_type', 'document_number', 'phone_number',
                  'expedition_date', 'name',
                  'lasts_name', 'email', 'city', 'address', 'professional_card', ]
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'expedition_date': 'Fecha de expedición',
                  'name': 'Nombres',
                  'phone_number': 'Telefóno/Célular',
                  'lasts_name': 'Apellidos',
                  'email': 'Correo electrónico',
                  'city': 'Ciudad / Municipio',
                  'address': 'Dirección de contacto',
                  'professional_card': 'Número Tarjeta Profecional (Abogado)'}

        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'expedition_date': forms.DateInput(format='%Y-%m-%d', attrs={'placeholder': 'digite la fecha', 'type': 'date'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
        }

    def __init__(self, *args, **kwargs):
        super(AbstractPersonAttorny, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Información Apoderado'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('attorny_type',
                               css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('document_type',
                               css_class='form-group col-md-4 mb-0'),
                        Column('document_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('expedition_date',
                               css_class='form-group col-md-4 mb-0'),
                        Column('professional_card',
                               css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('name', css_class='form-group col-md-6 mb-0'),
                        Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ), Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation',
                               css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-4 mb-0'),
                        Column('phone_number',
                               css_class='form-group col-md-4 mb-0'),
                        Column('address', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ), css_class='card-body'
                ), css_class="card mb-3",
            )
        )


class ConsecutiveFormatForm(forms.ModelForm):
    '''Custom consecutive number configuration form for admin page'''

    digits_range = (2, 12)

    def clean(self, *args, **kwargs):
        cleaned_data = super(ConsecutiveFormatForm, self).clean()

        if RecordCodeService.tokens[0][:-1] not in self.data['format']:
            raise ValidationError("El número consecutivo es requerido")
        if not self.data['digits']:
            raise ValidationError(
                "Número de dígitos del consecutivo es requerido")

        if not self.data['digits'].isdigit()  \
                or int(self.data['digits']) < ConsecutiveFormatForm.digits_range[0] \
                or int(self.data['digits']) > ConsecutiveFormatForm.digits_range[1]:
            raise ValidationError(
                "Valor o rango invalido para el número de dígitos del consecutivo")

        self.cleaned_data['format'] = RecordCodeService.compile(
            self.data['format'],
            self.data['digits'])
        return cleaned_data

    class Meta:
        fields = ('format', 'effective_date')

        widgets = {
            'format': ConsecutiveFormatWidget()
        }


class CalendarForm(forms.ModelForm):
    '''Custom non-working days configuration form for admin page'''

    def clean(self, *args, **kwargs):
        cleaned_data = super(CalendarForm, self).clean()

        if self.data['calendarData'].strip() and self.data['year']:
            events = json.loads(self.data['calendarData'])
            year = int(self.data['year'])
            CalendarService.update_calendar_days(year, events)

        return cleaned_data

    class Meta:
        widgets = {
            'name': NonWorkingCalendarWidget()
        }


def _get_filtered_permissions():
    perms = Permission.objects.all()
    perms = perms.exclude(Q(codename__contains='add_') | Q(codename__contains='change_')
                          | Q(codename__contains='delete_') | Q(codename__contains='view_'))
    return perms


class CustomGroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    permissions = forms.ModelMultipleChoiceField(
        _get_filtered_permissions(),
        widget=FilteredSelectMultiple(('permissions'), False),
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.',
        required=False
    )


class CustomUserChangeForm(UserChangeForm):

    user_permissions = forms.ModelMultipleChoiceField(
        _get_filtered_permissions(),
        widget=FilteredSelectMultiple(('user_permissions'), False),
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.',
        required=False
    )

class SignatureFlowForm(forms.ModelForm):

    id = forms.CharField(max_length=50, required=False, widget=SignatureFlowWidget(), label='Graph')

    def clean(self, *args, **kwargs):

        cleaned_data = super(SignatureFlowForm, self).clean()
        if self.data['id'] != -1:
            if self.data['graph'].strip():
                graph = json.loads(self.data['graph'])
                sf = SignatureFlowService.from_json(graph, self.cleaned_data['id'])

        return cleaned_data

    class Meta:
        model = SignatureFlow
        fields = ['name', 'description', 'id']
