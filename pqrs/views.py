import uuid
from django.db.models import query
from django.db.models.expressions import Value
from django.shortcuts import redirect, render
from requests.models import Request

from correspondence.models import ReceptionMode, RadicateTypes, Radicate, AlfrescoFile
from core.models import Attorny, AttornyType, Atttorny_Person, City, LegalPerson, Person, Office, DocumentTypes, PersonRequest, PersonType
from pqrs.models import PQRS,Type, PqrsContent,Type, SubType
from core.models import Attorny, AttornyType, Atttorny_Person, City, LegalPerson, Person, Office, DocumentTypes, PersonRequest, PersonType, RequestResponse
from pqrs.forms import LegalPersonForm, SearchPersonForm, PersonForm, PqrRadicateForm,PersonRequestForm,PersonFormUpdate,PersonRequestFormUpdate,PersonAttorny
from core.utils_db import process_email,get_system_parameter, get_json_system_parameter
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.postgres.search import SearchVector
from django.utils.crypto import get_random_string
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from core.utils_redis import add_to_redis, read_from_redis
from correspondence.services import ECMService
from core.services import RecordCodeService
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File

from pinax.eventlog.models import log, Log

import requests
import json
import os
import io
from docx import Document
import logging
import xlsxwriter
import re
import redis
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    rino_parameter = get_system_parameter('RINO_PQR_INFO')
    anonymous_applicant = get_system_parameter('RINO_PQR_ANONYMOUS_APPLICANT')
    normal_applicant = get_system_parameter('RINO_PQR_NORMAL_APPLICANT')
    private_applicant = get_system_parameter('RINO_PQR_PRIVATE_APPLICANT')
    return render(
        request,
        'pqrs/index.html', {
            'rino_parameter': rino_parameter.value,
            'anonymous_applicant': anonymous_applicant.value,
            'normal_applicant': normal_applicant.value,
            'private_applicant': private_applicant.value,
        })


def send_email_person(request, pk, pqrs_type):
    unique_id = get_random_string(length=32)
    toSave = json.dumps({
        "personPk": pk,
        "pqrs_type": pqrs_type
    })
    add_to_redis(unique_id, toSave, 'email')
    person = Person.objects.get(pk=pk)
    base_url = "{0}://{1}/pqrs/validate-email-person/{2}".format(
        request.scheme, request.get_host(), unique_id)
    person.url = base_url
    process_email('EMAIL_PQR_VALIDATE_PERSON', person.email, person)
    return render(request, 'pqrs/search_person_answer_form.html', context={'msg': 'Se ha enviado un correo electrónico con la información para registrar el caso'})


def validate_email_person(request, uuid_redis):
    redis_pk = read_from_redis(uuid_redis, 'email')
    if redis_pk is None:
        return render(request, 'pqrs/search_person_answer_form.html', context={ 'msg': 'El token ha caducado' })
    else:
        pk = json.loads(redis_pk)
        person = Person.objects.get(pk=pk["personPk"])
        if person is None:
            return render(request, 'pqrs/search_person_answer_form.html', context={'msg': 'El token es inválido'})
        else:
            pqrsTy = get_object_or_404(Type, id=int(pk["pqrs_type"]))
            pqrsObject=PQRS(pqr_type = pqrsTy,principal_person = person)
            pqrsObject.save()
            # url = reverse('pqrs:edit_person', kwargs={'pk': person.pk})
            # return HttpResponseRedirect(url)
            return redirect('pqrs:edit_person',pqrsObject.uuid,person.pk)
def search_person(request,pqrs_type,person_type):
    if person_type == 1:
        template_return = 'pqrs/search_person_form.html'
    elif person_type == 2:
        template_return = 'pqrs/search_legal_person_form.html'
    if request.method == 'POST':
        form = SearchPersonForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            if person_type == 1:
                qs = Person.objects.annotate(search=SearchVector(
                    'document_number', 'email', 'name'), ).filter(search=item)
                person_form = PersonForm()
            elif person_type == 2:
                qs = LegalPerson.objects.annotate(search=SearchVector(
                    'document_company_number', 'company_name'), ).filter(search=item)
                person_form = LegalPersonForm()
            if not qs.count():
                messages.warning(
                    request, "La búsqueda no obtuvo resultados. Registre la siguiente informacion para continuar con el proceso")
    else:
        form = SearchPersonForm()
        qs = None
        person_form = None

    return render(
        request,
        template_return,
        context={
            'form': form,
            'list': qs,
            'person_form': person_form,
            "pqrs_type": pqrs_type,
            'person_type': person_type})


def create_pqr_multiple(request, pqrs):
    pqrsoparent = get_object_or_404(PQRS, uuid=pqrs)
    person = get_object_or_404(Person, id=int(pqrsoparent.principal_person.id))

    if request.method == 'POST':
        print('ingresando')
        form = PqrRadicateForm(pqrsoparent.pqr_type, request.POST)
        print('form creado')
        if form.is_valid():
            instance = form.save(commit=False)
            instance.reception_mode = get_object_or_404(
                ReceptionMode, abbr='VIR')
            instance.type = get_object_or_404(RadicateTypes, abbr='PQR')
            instance.number = RecordCodeService.get_consecutive(
                RecordCodeService.Type.INPUT)
            instance.response_mode = person.request_response
            instance.person = person
            instance.pqrsobject = pqrsoparent
            radicate =  form.save()
            log(
                user=request.user,
                action="PQR_CREATED",
                obj=radicate,
                extra={
                    "number": radicate.number,
                    "message": "El radicado %s ha sido creado" % (radicate.number)
                }
            )
            query_url = "{0}://{1}/correspondence/radicate/{2}".format(
                request.scheme, request.get_host(), radicate.pk)
            instance.url = query_url
            process_email('EMAIL_PQR_CREATE', instance.person.email, instance)

            for fileUploaded in request.FILES.getlist('uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)

                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(
                    File(document_temp_file, name=fileUploaded.name))
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=radicate,
                                            name=os.path.splitext(fileUploaded.name)[0],
                                            extension=os.path.splitext(fileUploaded.name)[1])
                alfrescoFile.save()

                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(
                        request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")

            messages.success(request, "El radicado se ha creado correctamente")
            # url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
            # return redirect('pqrs:pqrs_finish_creation', radicate.pk)
            url = reverse('pqrs:pqrs_finish_creation', kwargs={'pk': radicate.pk})
            return HttpResponseRedirect(url)
        
        else:
            logger.error("Invalid create pqr form", form.is_valid(), form.errors)
            return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person})
    else:
        form = PqrRadicateForm(typePqr=pqrsoparent.pqr_type)
        form.person = person

    return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person})


def PQRSType(request, applicanType):
    pqrs_types = Type.objects.all()
    return render(
        request,
        'pqrs/pqrs_type.html',
        context={
            'types': pqrs_types,
            "applicant_type": applicanType
        })


def person_type(request, pqrs_type, applicanType):
    if applicanType == 1:
        rino_parameter = get_system_parameter('RINO_PQR_MESSAGE_DOCUMENT')
        person_type = PersonType.objects.all()
        return render(
            request, 'pqrs/person_type.html',
            context={
                'person_type_message': rino_parameter.value,
                'person_type': person_type,
                'pqrs_type': pqrs_type})
    else:
        pqrsTy = get_object_or_404(Type, id=int(pqrs_type))
        person_anonnymous = get_object_or_404(Person, id=1)
        pqrsObject = PQRS(pqr_type=pqrsTy, principal_person=person_anonnymous)
        pqrsObject.save()
        return redirect('pqrs:pqrs_create_multiple_person', pqrsObject.uuid)


def multi_create_request(request, person):
    pqrs_object = get_object_or_404(PQRS, uuid=int(person))
    if request.method == 'GET':
        document_type = DocumentTypes.objects.filter(
            name=pqrs_object.principal_person.document_type)[0].abbr
        context = {
            'document_type_abbr': document_type,
            'person': pqrs_object.principal_person,
            'pqrs_type_option': pqrs_object.pqr_type.id,
            'pqrs_type': person,
            'other_people': pqrs_object.multi_request_person.all()}
        return render(request, 'pqrs/multi_request_table.html', {'context': context})

    else:
        form = SearchPersonForm()
        qs = None
        person_form = None

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form})


def dete_person_request(request, pqrs_type, id):
    personsDelte = get_object_or_404(PersonRequest, id=id)
    personsDelte.delete()
    return redirect('pqrs:multi_request', pqrs_type)


class PqrDetailView(DetailView):
    model = Radicate
    template_name = 'pqrs/pqr_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailView, self).get_context_data(**kwargs)
        context['logs'] = Log.objects.all().filter(object_id=self.kwargs['pk'])
        return context


class PqrFinishCreation(DetailView):
    model = Radicate
    template_name = 'pqrs/pqr_finish_creation.html'

    def get_context_data(self, **kwargs):
        context = super(PqrFinishCreation, self).get_context_data(**kwargs)
        context['file'] = AlfrescoFile.objects.all().filter(
            radicate=self.kwargs['pk'])
        objectPqrs = PQRS.objects.filter(
            principal_person=context['radicate'].person.pk)[0]
        personrequest = objectPqrs.multi_request_person.all()
        if personrequest:
            context['personRequest'] = personrequest
        if context['radicate'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(
                person=context['radicate'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context

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


def select(requests):
    return render(requests, 'pqrs/select.html', {})


class RadicateInbox(ListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_inbox.html'

    def get_queryset(self):
        queryset = super(RadicateInbox, self).get_queryset()
        queryset = queryset.filter(subtype__isnull=False, pqrsobject__status=PQRS.Status.CREATED)
        return queryset

class RadicateMyInbox(ListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_inbox.html'

    def get_queryset(self):
        queryset = super(RadicateMyInbox, self).get_queryset()
        queryset = queryset.filter(current_user = self.request.user, subtype__isnull=False)
        return queryset

class PqrDetailProcessView(DetailView):
    model = Radicate
    template_name = 'pqrs/pqr_detail_process.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailProcessView, self).get_context_data(**kwargs)
        context['logs'] = Log.objects.all().filter(object_id=self.kwargs['pk'])
        # context['file'] = AlfrescoFile.objects.all().filter(
        #     radicate=self.kwargs['pk'])
        objectPqrs = PQRS.objects.filter(
            principal_person=context['radicate'].person.pk)[0]
        personrequest = objectPqrs.multi_request_person.all()
        if personrequest:
            context['personRequest'] = personrequest
        if context['radicate'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(
                person=context['radicate'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context


def procedure_conclusion(request):
    
    procedure_conclusion_param = get_json_system_parameter('PROCEDURE_CONCLUSION')
    template = request.GET['template']
    view_name = request.GET['redirect']
    context = {
        'procedure_conclusion': procedure_conclusion_param,
        'url' : template+':'+view_name
    }
    return render(request, 'pqrs/conclusion.html', context)