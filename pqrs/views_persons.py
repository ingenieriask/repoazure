import uuid
from django.shortcuts import redirect, render
from numpy import number, subtract
from pqrs.models import PQRS, Type, Type
from core.models import Attorny, AttornyType, Atttorny_Person, City, LegalPerson, \
    Person, DocumentTypes, PersonRequest
from django_mailbox.models import Message
from pqrs.forms import LegalPersonForm, PersonForm, \
    PersonRequestForm, PersonFormUpdate, PersonRequestFormUpdate, \
    PersonAttorny

from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from core.utils_redis import add_to_redis, read_from_redis

import logging

logger = logging.getLogger(__name__)

# PERSONS Views
class PersonCreateView(CreateView):
    model = Person
    form_class = PersonForm
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        #self.object.disabilities = form['']
        self.object.save()
        form.save_m2m()
        pqrsTy = get_object_or_404(Type, id=int(self.kwargs['pqrs_type']))
        pqrsObject = PQRS(pqr_type=pqrsTy, principal_person=self.object)
        pqrsObject.save()
        if self.object.attornyCheck or form['document_type'].value() == 4:
            return redirect('pqrs:create_person_attorny', pqrsObject.uuid)
        return redirect('pqrs:multi_request', pqrsObject.uuid)


class LegalPersonCreateView(CreateView):
    model = LegalPerson
    form_class = LegalPersonForm
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = LegalPerson(
            verification_code=form['verification_code'].value(),
            company_name=form['company_name'].value(),
            document_company_number=form['document_company_number'].value(),
            document_number=form['document_company_number'].value(),
            email=form['email'].value(),
            representative=f"{form['name'].value()} {form['lasts_name'].value()}",
            document_type_company=DocumentTypes.objects.filter(
                id=int(form['document_type_company'].value()))[0],
        )
        self.object.save()
        pqrsTy = get_object_or_404(Type, id=int(self.kwargs['pqrs_type']))
        person_legal = Person(
            name=form['name'].value(),
            lasts_name=form['lasts_name'].value(),
            document_type=DocumentTypes.objects.filter(
                id=int(form['document_type'].value()))[0],
            document_number=form['document_number'].value(),
            expedition_date=form['expedition_date'].value(),
            email=form['email'].value(),
            city=City.objects.filter(id=int(form['city'].value()))[0],
            phone_number=form['phone_number'].value(),
            address=form['address'].value(),
            parent=self.object
        )
        person_legal.save()
        pqrsObject = PQRS(pqr_type=pqrsTy, principal_person=person_legal)
        pqrsObject.save()
        return redirect('pqrs:pqrs_create_multiple_person', pqrsObject.uuid)


class PersonRequestCreateView(CreateView):
    model = PersonRequest
    form_class = PersonRequestForm
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        pqrsObject = get_object_or_404(PQRS, uuid=self.kwargs['pqrs_type'])
        pqrsObject.multi_request_person.add(self.object)
        return redirect('pqrs:multi_request', pqrsObject.uuid)

    def get_form_kwargs(self):
        kwargs = super(PersonRequestCreateView, self).get_form_kwargs()
        # update the kwargs for the form init method with yours
        kwargs.update(self.kwargs)  # self.kwargs contains all url conf params
        return kwargs


class PersonDetailView(DetailView):
    model = Person


class PersonUpdateViewNew(UpdateView):
    model = Person
    form_class = PersonFormUpdate
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        return redirect('pqrs:multi_request', self.kwargs['pqrs_type'])

    def get_form_kwargs(self):
        kwargs = super(PersonUpdateViewNew, self).get_form_kwargs()
        # update the kwargs for the form init method with yours
        kwargs.update(self.kwargs)  # self.kwargs contains all url conf params
        return kwargs


class PersonUpdateViewNewRequest(UpdateView):
    model = PersonRequest
    form_class = PersonRequestFormUpdate
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect('pqrs:multi_request', self.kwargs['pqrs_type'])

    def get_form_kwargs(self):
        kwargs = super(PersonUpdateViewNewRequest, self).get_form_kwargs()
        # update the kwargs for the form init method with yours
        kwargs.update(self.kwargs)  # self.kwargs contains all url conf params
        return kwargs


class PersonAtronyCreate(CreateView):
    model = Attorny
    form_class = PersonAttorny
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        pqrsObject = get_object_or_404(PQRS, uuid=self.kwargs['pqrs_type'])
        attorny_type = get_object_or_404(
            AttornyType, id=int(form['attorny_type'].value()))
        atornyPerson = Atttorny_Person(
            attorny=self.object, person=pqrsObject.principal_person, attorny_type=attorny_type)
        atornyPerson.save()
        return redirect('pqrs:multi_request', pqrsObject.uuid)

    def get_form_kwargs(self):
        kwargs = super(PersonAtronyCreate, self).get_form_kwargs()
        # update the kwargs for the form init method with yours
        kwargs.update(self.kwargs)  # self.kwargs contains all url conf params
        return kwargs


class PersonUpdateView(UpdateView):
    model = Person
    form_class = PersonForm
    template_name = 'pqrs/person_form.html'

    def get(request, *args, **kwargs):
        pk = read_from_redis(kwargs.get('uuid'), 'email')
        if pk is not None and int(pk.decode()) == int(kwargs['pk']):
            return super().get(request, *args, **kwargs)
        else:
            messages.error(request, "error de validacion")
            return render(request, 'pqrs/search_person_answer_form.html', context={'msg': 'El token es inválido'})
