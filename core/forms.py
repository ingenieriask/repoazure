from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, ButtonHolder, Button, Div, HTML
from core.models import Person
from crispy_forms.layout import Field
from core.utils import get_field_value
from core.widgets import ConsecutiveFormatWidget
from core.services import RecordCodeService

class CustomFileInput(Field):
    template = 'core/custom_fileinput.html'


class AbstractPersonForm(forms.ModelForm):

    email_confirmation = forms.CharField(label='Confirmación del correo electrónico', required=True)

    def clean_email_confirmation(self):
        cd = self.cleaned_data
        if (get_field_value(cd, 'email_confirmation') != get_field_value(cd, 'email')):
            raise forms.ValidationError('El correo de validación no coincide con el correo')
        return get_field_value(cd, 'email_confirmation')

    def clean(self):
        cleaned_data = super().clean()
        cleaned_address = cleaned_data.get('address')
        cleaned_email = cleaned_data.get('email')
        if cleaned_address is None and cleaned_email is None:
            raise forms.ValidationError('Por favor ingrese la dirección de contacto o el correo electrónico')
        return cleaned_data

    class Meta:
        model = Person

        fields = ['document_type', 'document_number', 'name', 'email', 'city', 'address', 'parent', 'preferencial_population', 'conflict_victim', 'disabilities', 'ethnic_group']
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
        super(AbstractPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Datos básicos'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('document_type', css_class='form-group col-md-6 mb-0'),
                        Column('document_number', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('name', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Datos de contacto'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-6 mb-0'),
                        Column('address', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(Div(HTML('Población Especial'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('preferencial_population', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('conflict_victim', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('disabilities', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('ethnic_group', css_class='form-group col-md-12 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
                ),
                css_class="card mb-3",
            )
        )

class ConsecutiveFormatForm(forms.ModelForm):
    '''Custom format for admin page'''

    digits_range = (2, 12)

    def clean(self, *args, **kwargs):
        cleaned_data = super(ConsecutiveFormatForm, self).clean()

        if RecordCodeService.tokens[0][:-1] not in self.data['format']:
            raise ValidationError("El número consecutivo es requerido")
        if not self.data['digits']:
            raise ValidationError("Número de dígitos del consecutivo es requerido")
         
        if not self.data['digits'].isdigit()  \
            or int(self.data['digits']) < ConsecutiveFormatForm.digits_range[0] \
            or int(self.data['digits']) > ConsecutiveFormatForm.digits_range[1]:
            raise ValidationError("Valor o rango invalido para el número de dígitos del consecutivo")

        print("self.data['digits']:", self.data['digits'])

        self.cleaned_data['format'] = RecordCodeService.compile(
                                            self.data['format'], 
                                            self.data['digits'])
        return cleaned_data

    class Meta:
        fields = ('format', 'effective_date')

        widgets = {
            'format': ConsecutiveFormatWidget()
        }