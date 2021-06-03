from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, ButtonHolder, Button, Div, HTML
from core.models import Person,Disability,PreferencialPopulation
from crispy_forms.layout import Field
from core.utils import get_field_value
from core.widgets import ConsecutiveFormatWidget
from core.services import RecordCodeService

class CustomFileInput(Field):
    template = 'core/custom_fileinput.html'


class AbstractPersonForm(forms.ModelForm):

    email_confirmation = forms.CharField(label='Confirmación del correo electrónico', required=True)
    preferencial_population=forms.ModelMultipleChoiceField(
        queryset=PreferencialPopulation.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Población Preferencial (Selección Múltiple)')
    disabilities= forms.ModelMultipleChoiceField(
        queryset=Disability.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Población en situación de discapacidad (Selección Múltiple)')
    
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

        fields = ['document_type', 'document_number','phone_number',
                 'request_response','expedition_date','person_type', 'name',
                  'lasts_name', 'email', 'city', 'address', 'parent', 'preferencial_population',
                   'conflict_victim', 'disabilities', 'ethnic_group']
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'expedition_date': 'Fecha de expedición',
                  'request_response': '¿Por cual medio desea recibir su respuesta?',
                  'name': 'Nombres',
                   'phone_number': 'Telefóno/Célular',
                  'lasts_name': 'Apellidos', 
                   'email': 'Correo electrónico',
                  'person_type': 'Tipo persona',
                  'city': 'Ciudad / Municipio', 'address': 'Dirección de contacto',
                  'parent': 'Entidad',
                  'conflict_victim': 'Población víctima del conflicto armado',
                  'ethnic_group': 'Grupo Étnico'}
        
        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'request_response': forms.Select(attrs={'class': 'selectpicker'}),
            'person_type': forms.Select(attrs={'class': 'selectpicker'}),
            'expedition_date': forms.DateInput(format='%Y-%m-%d',attrs={ 'placeholder': 'digite la fecha','type': 'date'} ),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'parent': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'conflict_victim': forms.Select(attrs={'class': 'selectpicker', 'data-size': '7'}),
            'ethnic_group': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
        }

    def __init__(self, *args, **kwargs):
        super(AbstractPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(HTML('Información General'),
                    css_class='card-header'),
                Div(
                    
                    Row(
                        Column('name', css_class='form-group col-md-6 mb-0'),
                        Column('lasts_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('document_type', css_class='form-group col-md-4 mb-0'),
                        Column('document_number', css_class='form-group col-md-4 mb-0'),
                        Column('expedition_date', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row( Column('person_type', css_class='form-group col-md-4 mb-0'),)
                    ,css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(
                Div(HTML('Información de contacto'),
                    css_class='card-header'),
                Div(
                    Row( Column('request_response', css_class='form-group col-md-6 mb-0'),),
                    Row(
                        Column('email', css_class='form-group col-md-6 mb-0'),
                        Column('email_confirmation', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('city', css_class='form-group col-md-4 mb-0'),
                        Column('phone_number', css_class='form-group col-md-4 mb-0'),
                        Column('address', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),css_class='card-body'
                ), css_class="card mb-3",
            ),
            Div(Div(HTML('Población Especial'),
                    css_class='card-header'),
                Div(
                    Row(
                        Column('conflict_victim', css_class='form-group col-md-6 mb-0'),
                        Column('ethnic_group', css_class='form-group col-md-6 mb-0'),

                        css_class='form-row'
                    ),
                    Row(
                        Column('preferencial_population', css_class='form-group col-md-6 mb-0'),
                        Column('disabilities', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
                ),
                
                css_class="card mb-3",
            ),
        )
    
    def save(self, commit=True):
        instance = forms.ModelForm.save(self, False)
        old_save_m2m = self.save_m2m
        def save_m2m():
            old_save_m2m()
            instance.person_set.clear()
            for disability in self.cleaned_data['disabilities']:
                b = Disability.objects.get(name=disability )
                print(disability,b)
                instance.person_set.add(b)
            for prefe_popu in self.cleaned_data['preferencial_population']:
                pre_po = Disability.objects.get(name=prefe_popu )
                print(prefe_popu,pre_po)
                instance.person_set.add(prefe_popu)

        self.save_m2m = save_m2m
        instance.save()
        self.save_m2m()


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