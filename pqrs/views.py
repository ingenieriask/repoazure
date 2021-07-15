import uuid
from django.db.models import query
from django.db.models.expressions import Value
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from numpy import number, subtract
from requests.models import Request
from correspondence.models import ReceptionMode, RadicateTypes, Radicate, AlfrescoFile, ProcessActionStep
from pqrs.models import PQRS,Type, PqrsContent,Type, SubType, InterestGroup
from core.models import Attorny, AttornyType, Atttorny_Person, City, LegalPerson, \
    Person, Office, DocumentTypes, PersonRequest, PersonType 
from pqrs.forms import ChangeClassificationForm, LegalPersonForm, PqrsConsultantForm, SearchUniquePersonForm, PersonForm, \
    PqrRadicateForm, PersonRequestForm, PersonFormUpdate, PersonRequestFormUpdate, \
    PersonAttorny, PqrsConsultantForm, SearchLegalersonForm, PqrsExtendRequestForm, RequestAnswerForm, \
    PqrsAnswerForm

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.postgres.search import SearchVector
from django.utils.crypto import get_random_string
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from core.utils_redis import add_to_redis, read_from_redis
from correspondence.services import ECMService
from core.services import PdfCreationService
from core.services import NotificationsHandler, RecordCodeService, Recipients
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import default_storage
from django.core.files import File
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from core.decorators import has_any_permission
from django.db.models import Q
from datetime import date
from core.utils_services import FormatHelper
from django.utils.http import urlencode

from pinax.eventlog.models import log, Log
from crum import get_current_user
from django.utils.decorators import method_decorator
from core.decorators import has_radicate_permission
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

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
from core.services import SystemParameterHelper
import zipfile

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    rino_parameter = SystemParameterHelper.get('RINO_PQR_INFO')
    anonymous_applicant = SystemParameterHelper.get('RINO_PQR_ANONYMOUS_APPLICANT')
    normal_applicant = SystemParameterHelper.get('RINO_PQR_NORMAL_APPLICANT')
    private_applicant = SystemParameterHelper.get('RINO_PQR_PRIVATE_APPLICANT')
    return render(
        request,
        'pqrs/index.html', {
            'rino_parameter': rino_parameter.value,
            'anonymous_applicant': anonymous_applicant.value,
            'normal_applicant': normal_applicant.value,
            'private_applicant': private_applicant.value,
        })


def send_email_extend_request(request, instance):
    unique_id = get_random_string(length=32)
    toSave = json.dumps({
        "radicatePk": instance.pk
    })
    add_to_redis(unique_id, toSave, 'radicate')
    base_url = "{0}://{1}/pqrs/answer-request-email/{2}".format(request.scheme, request.get_host(), unique_id)
    instance.url = base_url
    NotificationsHandler.send_notification('EMAIL_PQR_EXTEND', instance, Recipients(instance.person.email))


def send_email_person(request, pk, pqrs_type):
    unique_id = get_random_string(length=32)
    toSave = json.dumps({
        "personPk": pk,
        "pqrs_type": pqrs_type
    })
    add_to_redis(unique_id, toSave, 'email')
    person = Person.objects.get(pk=pk)
    base_url = "{0}://{1}/pqrs/validate-email-person/{2}".format(request.scheme, request.get_host(), unique_id)
    person.url = base_url
    NotificationsHandler.send_notification('EMAIL_PQR_VALIDATE_PERSON', person,
                                            Recipients(person.email))
    return render(request, 'pqrs/search_person_answer_form.html', context={'msg': 'Se ha enviado un correo electrónico con la información para registrar el requerimiento'})


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

def pqrs_answer_request_email(request, uuid_redis):
    redis_pk = read_from_redis(uuid_redis, 'radicate')
    get_args_str = urlencode({'template': 'PROCEDURE_CONCLUSION', 'destination': 'index'})
    if redis_pk is None:
        return HttpResponseRedirect(reverse('pqrs:conclusion')+'?'+get_args_str)
    else:
        pk = json.loads(redis_pk)
        print(pk["radicatePk"])
        pqrs = Radicate.objects.get(pk=pk["radicatePk"])
        if pqrs is None:
            return HttpResponseRedirect(reverse('pqrs:conclusion')+'?'+get_args_str)
        else:
            return redirect('pqrs:answer_request',pqrs.pk)


def search_person(request,pqrs_type,person_type):
    if request.method == 'POST':
        if person_type == 1:
            form = SearchUniquePersonForm(request.POST)
        elif person_type == 2:
            form = SearchLegalersonForm(request.POST)
        if form.is_valid():
            if person_type == 1:
                doc_num = form['doc_num'].value()
                document_type = form['document_type'].value()
                qs = Person.objects.filter(
                    Q(document_number=doc_num) & 
                    Q(document_type=document_type))
                person_form = PersonForm()
            elif person_type == 2:
                doc_num = form['doc_num'].value()
                document_type_company = form['document_type_company'].value()
                verification_digit = form['verification_digit'].value()
                qs = LegalPerson.objects.all().filter(
                    Q(document_number=doc_num) &
                    Q(document_type_company=document_type_company) &
                    Q(verification_code=verification_digit))
                person_form = LegalPersonForm()
            if not qs.count():
                messages.warning(
                    request, "La búsqueda no obtuvo resultados. Registre la siguiente informacion para continuar con el proceso")
    else:
        qs = None
        person_form = None
        formeny = {'1': SearchUniquePersonForm(), '2': SearchLegalersonForm()}
        form = formeny[str(person_type)]
    return render(
        request,
        'pqrs/search_person_form.html',
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
        form = PqrRadicateForm(pqrsoparent.pqr_type, request.POST)
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
            folder_id = ECMService.create_folder(radicate.number)
            radicate.folder_id = folder_id
            radicate.save()

            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Creación'
            action.detail = 'El radicado %s ha sido creado' % (radicate.number) 
            action.radicate = radicate
            action.save()

            log(
                user=request.user,
                action="PQR_CREATED",
                obj=action,
                extra={
                    "number": radicate.number,
                    "message": "El radicado %s ha sido creado" % (radicate.number)
                }
            )
            query_url = "{0}://{1}/correspondence/radicate/{2}".format(request.scheme, request.get_host(), radicate.pk)
            instance.url = query_url
            NotificationsHandler.send_notification('EMAIL_PQR_CREATE', instance, 
                                                    Recipients(instance.person.email))

            for fileUploaded in request.FILES.getlist('pqrs_creation_uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)

                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name), radicate.folder_id)
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=radicate,
                                            name=os.path.splitext(fileUploaded.name)[0],
                                            extension=os.path.splitext(fileUploaded.name)[1],
                                            size=int(fileUploaded.size/1000))
                alfrescoFile.save()

                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(
                        request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")

            PdfCreationService.create_pqrs_confirmation_label(radicate)
            PdfCreationService.create_pqrs_summary(radicate)
            messages.success(request, "El radicado se ha creado correctamente")
            # url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
            # return redirect('pqrs:pqrs_finish_creation', radicate.pk)
            url = reverse('pqrs:pqrs_finish_creation', kwargs={'pk': radicate.pk})
            return HttpResponseRedirect(url)
        
        else:
            print(form.errors)
            logger.error("Invalid create pqr form", form.is_valid(), form.errors)
            return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person, 'pqrs': pqrs})
    else:
        form = PqrRadicateForm(typePqr=pqrsoparent.pqr_type)
        form.person = person

    return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person, 'pqrs': pqrs})


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
        rino_parameter = SystemParameterHelper.get('RINO_PQR_MESSAGE_DOCUMENT')
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
        form = SearchUniquePersonForm()
        qs = None
        person_form = None

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form})


def dete_person_request(request, pqrs_type, id):
    personsDelte = get_object_or_404(PersonRequest, id=id)
    personsDelte.delete()
    return redirect('pqrs:multi_request', pqrs_type)

def select(requests):
    return render(requests, 'pqrs/select.html', {})

def pqrsConsultan(request):
    message_pqrs_consultant = SystemParameterHelper.get('RINO_PQRSD_CONSULTANT_MESSAGE')
    if request.method == 'POST':
        form = PqrsConsultantForm(request.POST)
        if form.is_valid():
            num_rad = form['num_rad'].value()
            doc_num = form['doc_num'].value()
            pqrsContent = PqrsContent.objects.filter(
                Q(number=num_rad) & Q(person__document_number=doc_num))
            if pqrsContent:
                return redirect('pqrs:consultation_result', pqrsContent[0].id)
                #render to send token and show resutl
            else:
                messages.error( request, "La PQRDS no existe")
    else:
        form = PqrsConsultantForm()
    return render(
        request, 'pqrs/consultant_form.html', 
        context={
            'form': form,
            "messageHead": message_pqrs_consultant.value})

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

class RadicateListView(ListView):
    paginate_by = 5

    def get_paginate_by(self, queryset):
        print('paginate_by', self.request.GET.get("paginate_by", self.paginate_by))
        return self.request.GET.get("paginate_by", self.paginate_by)

    
    def filter(func):

        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            term = args[0].request.GET.get('filter', None)
            if term == 'None':
                term = None
            if term:
                print(term)
                queryset = queryset.filter(Q(number__contains=term) | 
                Q(person__name__icontains=term) | Q(subject__icontains=term) | 
                Q(subtype__type__name__icontains=term) | Q(subtype__name__icontains=term) |
                Q(pqrsobject__status__icontains=term))
            return queryset

        return wrapper

    def get_context_data(self, **kwargs):
        context = super(RadicateListView, self).get_context_data(**kwargs)
        term = self.request.GET.get('filter', None)
        if term:
            context['filter'] = term
        return context

#@method_decorator(login_required, name='dispatch')
@method_decorator(has_any_permission(['auth.receive_external']), name='dispatch')
class RadicateInbox(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateInbox, self).get_queryset()
        queryset = queryset.filter(subtype__isnull=False, pqrsobject__status=PQRS.Status.CREATED)
        return queryset

class RadicateMyInbox(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_my_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateMyInbox, self).get_queryset()
        queryset = queryset.filter(current_user = self.request.user, subtype__isnull=False)
        return queryset

class RadicateMyReported(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_reported_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateMyReported, self).get_queryset()
        queryset = queryset.filter(reported_people = self.request.user, subtype__isnull=False)
        return queryset

@method_decorator(has_radicate_permission([]), name='dispatch')
class PqrDetailProcessView(DetailView):
    model = PqrsContent
    template_name = 'pqrs/pqr_detail_process_actions.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailProcessView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        if context['pqrscontent'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(person=context['pqrscontent'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context

@method_decorator(has_radicate_permission([]), name='dispatch')
class PqrDetailAssignView(DetailView):
    model = PqrsContent
    template_name = 'pqrs/pqr_detail_process_actions_assign.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailAssignView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        if context['pqrscontent'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(person=context['pqrscontent'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context

@method_decorator(has_radicate_permission([]), name='dispatch')
class PqrDetailReportedView(DetailView):
    model = PqrsContent
    template_name = 'pqrs/pqr_detail_process.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailReportedView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        if context['pqrscontent'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(person=context['pqrscontent'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context

def procedure_conclusion(request):
    obj = {}
    if 'pk' in request.GET:
        obj = PqrsContent.objects.get(pk=request.GET['pk'])
        obj.date_radicated = obj.date_radicated.strftime("%d/%m/%y")
        obj.date_assignation = date.today().strftime("%d/%m/%y")
        obj.pqrsobject.status_str = str(obj.pqrsobject.get_status_str())

        reported_people_str = ''
        for person in obj.reported_people.all():
            reported_people_str += person.username + ' - ' + person.first_name + ' ' + person.last_name + '<br/>'

        obj.reported_people_str = reported_people_str
    template = SystemParameterHelper.get_json(request.GET['template'])
    
    template['title'] = FormatHelper.replace_data(template['title'], obj)
    template['body'] = FormatHelper.replace_data(template['body'], obj)
    destination = request.GET['destination']
    context = {
        'procedure_conclusion': template,
        'url' : destination
    }
    return render(request, 'pqrs/conclusion.html', context)


class PqrsConsultationResult(DetailView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/consultation_result.html'
    
    def get_context_data(self, **kwargs):
        context = super(PqrsConsultationResult, self).get_context_data(**kwargs)
        context['answers'] = Radicate.objects.filter(parent=context['pqrs'].id, 
                                                     classification=Radicate.Classification.COMPLETE_ANSWER)
        return context


def pqrs_extend_request(request, pk):
    
    radicate = PqrsContent.objects.get(pk=pk) #get_object_or_404(PqrsContent, id=pk)

    if request.method == 'POST':
        
        form = PqrsExtendRequestForm(radicate, request.POST)

        if form.is_valid():
            
            instance = form.save(commit=False)
            instance.number = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
            instance.type = radicate.type
            instance.record = radicate.record
            instance.person = radicate.person
            instance.reception_mode = radicate.reception_mode
            instance.office = radicate.office
            instance.doctype = radicate.doctype
            instance.parent = radicate
            instance.classification = Radicate.Classification.AMPLIATION_REQUEST
            
            instance.save()
            folder_id = ECMService.create_folder(instance.number)
            instance.folder_id = folder_id
            instance.save()

            instance.date_radicated_formated = radicate.date_radicated.strftime('%Y-%m-%d')
            instance.original_number = radicate.number
            send_email_extend_request(request, instance)
            
            
            for fileUploaded in request.FILES.getlist('uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)

                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name), instance.folder_id)
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=instance,
                                            name=os.path.splitext(fileUploaded.name)[0],
                                            extension=os.path.splitext(fileUploaded.name)[1],
                                            size=int(fileUploaded.size/1000))
                alfrescoFile.save()

                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(
                        request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")


            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Creación'
            action.detail = 'El radicado %s ha sido creado' % (instance.number) 
            action.radicate = instance
            action.save()

            log(
                user=request.user,
                action="RADICATE_CREATED",
                obj=action,
                extra={
                    "number": instance.number,
                    "message": "El radicado %s ha sido creado" % (instance.number)
                }
            )

            ## log de solicitud de ampliación de información del radicado original
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Solicitud de ampliación de información'
            action.detail = 'Se ha solicitado ampliación de información al radicado %s' % (instance.parent.number) 
            action.radicate = instance.parent
            action.save()

            messages.success(request, "La solicitud de ampliación se ha creado correctamente")
            return redirect('pqrs:detail_pqr', pk)

        return HttpResponseRedirect(request.path_info)
        
    else:
        initial_values = {
            'number': radicate.number,
            'person_type' : radicate.person.person_type,
            'document_type' : radicate.person.document_type,
            'document_number' : radicate.person.document_number,
            'expedition_date_last_digit' : radicate.person.expedition_date,
            'name_company_name' : radicate.person.name,
            'lasts_name_representative' : radicate.person.lasts_name,
            'email' : radicate.person.email,
            'address' : radicate.person.address,
            'phone_number' : radicate.person.phone_number,
            'city' : radicate.person.city,
            'subject' : 'Ampliación de solicitud - ' + radicate.subject,
        }
        
        if radicate.person.person_type.abbr == 'PJ':
            initial_values['name_company_name'] = radicate.person.parent.company_name
            initial_values['lasts_name_representative'] = radicate.person.parent.representative
            initial_values['expedition_date_last_digit'] = radicate.person.parent.verification_code
            initial_values['document_number'] = radicate.person.parent.document_company_number
            initial_values['document_type'] = radicate.person.parent.document_type_company
            
        form = PqrsExtendRequestForm(radicate, initial=initial_values)
        return render(request, 'pqrs/extend_request.html', context={'form': form, 'radicate': radicate})
    
def pqrs_associate_request(request, pk):
    
    radicate = PqrsContent.objects.get(pk=pk) 
    if request.method == 'POST':
        number = request.POST.get('radicate_number')
        classification = request.POST.get('kind_association')
        error = False
        if number is None or not number:
            messages.error(request, "El número de radicado es requerido")
            error = True
        if classification is None or not classification:
            messages.error(request, "El tipo de trámite es requerido")
            error = True

        if error == False:
            try:
                instance = Radicate.objects.get(number = number) 
                instance.parent = radicate
                instance.classification = classification
                instance.save()

                action = ProcessActionStep()
                action.user = get_current_user()
                action.action = 'Asociación'
                action.detail = 'El radicado %s ha sido asociado al radicado %s' % (instance.number, radicate.number) 
                action.radicate = instance
                action.save()

                log(
                    user=request.user,
                    action="RADICATE_ASSOCIATED",
                    obj=action,
                    extra={
                        "number": instance.number,
                        "message": 'El radicado %s ha sido asociado al radicado %s' % (instance.number, radicate.number) 
                    }
                )

                ## log de solicitud de ampliación de información del radicado original
                action = ProcessActionStep()
                action.user = get_current_user()
                action.action = 'Solicitud de ampliación de información'
                action.detail = 'El radicado %s ha sido asociado al radicado %s' % (instance.number, radicate.number) 
                action.radicate = instance.parent
                action.save()

                messages.success(request, "La solicitud de asociación se ha procesado correctamente")
                return redirect('pqrs:detail_pqr', pk)
            except:
                messages.error(request, "No se ha encontrado el radicado seleccionado")
        return HttpResponseRedirect(request.path_info)
    else:
        association_options = []
        for opt in Radicate.Classification:
            if opt != Radicate.Classification.PQR:
                association_options.append({'key': opt.value, 'value': opt.label})
        return render(request, 'pqrs/associate_radicate.html', context={'radicate': radicate, 'association_options': association_options})
    
    
def pqrs_answer_request(request, pk):
    
    radicate = get_object_or_404(Radicate, id=pk)
    
    if request.method == 'POST':
        
        form = RequestAnswerForm(request.POST)
        if form.is_valid():
            
            instance = form.save(commit=False)
            instance.number = RecordCodeService.get_consecutive(
                RecordCodeService.Type.INPUT)
            instance.type = radicate.type
            instance.record = radicate.record
            instance.person = radicate.person
            instance.reception_mode = radicate.reception_mode
            instance.office = radicate.office
            instance.doctype = radicate.doctype
            instance.subject = radicate.subject
            instance.parent = radicate.parent
            instance.classification = Radicate.Classification.AMPLIATION_ANSWER
            
            new_radicate = instance.save()
            folder_id = ECMService.create_folder(instance.number)
            instance.folder_id = folder_id
            instance.save()
            
            for fileUploaded in request.FILES.getlist('uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)

                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name), instance.folder_id)
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=new_radicate,
                                            name=os.path.splitext(fileUploaded.name)[0],
                                            extension=os.path.splitext(fileUploaded.name)[1],
                                            size=int(fileUploaded.size/1000))
                alfrescoFile.save()

                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")

            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Creación'
            action.detail = 'El radicado %s ha sido creado' % (instance.number) 
            action.radicate = instance
            action.save()

            log(
                user=request.user,
                action="RADICATE_CREATED",
                obj=action,
                extra={
                    "number": instance.number,
                    "message": "El radicado %s ha sido creado" % (instance.number)
                }
            )

            ## log de respuesta del radicado de solicitud de ampliación de información
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Respuesta'
            action.detail = 'El radicado %s ha sido respondido' % (radicate.number) 
            action.radicate = radicate
            action.save()

            ## log de respuesta del radicado original de la solicitud de ampliación de información
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Respuesta'
            action.detail = 'El radicado %s ha sido respondido' % (instance.parent.number) 
            action.radicate = instance.parent
            action.save()

            get_args_str = urlencode({'template': 'PROCEDURE_CONCLUSION', 'destination': 'index'})
            return HttpResponseRedirect(reverse('pqrs:conclusion')+'?'+get_args_str)
            
        return HttpResponseRedirect(request.path_info)
                
    else:
        
        form = RequestAnswerForm(initial={'number' : radicate.number})
        return render(request, 'pqrs/answer_request.html', context={'form': form, 'radicate': radicate})
    
    
def get_thumbnail(request):

    cmis_id = request.GET.get('cmis_id')
    prev_response = ECMService.get_thumbnail(cmis_id)
    if prev_response:
        return HttpResponse(prev_response, content_type="image/jpeg")

    return HttpResponse(default_storage.open('tmp/default.jpeg').read(), content_type="image/jpeg")    
    
def pqrs_answer(request, pk, actualPk):
    radicate = get_object_or_404(Radicate, id=actualPk)
    if request.method == 'POST':
        radicate.number = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
        radicate.folder_id = ECMService.create_folder(radicate.number)
        radicate.classification = Radicate.Classification.COMPLETE_ANSWER
        radicate.save()
        PdfCreationService.create_radicate_answer(radicate, True)

        ## log de respuesta del radicado de solicitud de ampliación de información
        action = ProcessActionStep()
        action.user = get_current_user()
        action.action = 'Respuesta'
        action.detail = 'La PQRSD %s ha sido respondida con el radicado %s' % (radicate.number, radicate.number) 
        action.radicate = radicate
        action.save()
        messages.success(request, "El radicado se ha creado correctamente")
    
        return redirect('pqrs:detail_pqr', pk)
    else:
        cmis = AlfrescoFile.objects.get(radicate=actualPk)
        return render(request, 'pqrs/answer_radicate_form.html', context={'radicate': radicate, 'cmis': cmis.cmis_id})

def pqrs_answer_preview(request, pk):
    
    radicate = get_object_or_404(PqrsContent, id=pk)

    if request.method == 'POST':
        
        form = PqrsAnswerForm(radicate, request.POST)

        if form.is_valid():
            
            instance = form.save(commit=False)
            instance.type = radicate.type
            instance.record = radicate.record
            instance.person = radicate.person
            instance.reception_mode = radicate.reception_mode
            instance.office = radicate.office
            instance.doctype = radicate.doctype
            instance.parent = radicate
            instance.observation = radicate.observation
            instance.subject = radicate.subject
            ### se crea un identificador de folder temporal
            instance.folder_id = '5ce20d5c-f92b-4e77-98ce-038c0dd5ae51'
            
            new_radicate = instance.save()
            
            for fileUploaded in request.FILES.getlist('answer_uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)

                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name), instance.folder_id)
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=new_radicate,
                                            name=os.path.splitext(fileUploaded.name)[0],
                                            extension=os.path.splitext(fileUploaded.name)[1],
                                            size=int(fileUploaded.size/1000))
                alfrescoFile.save()

                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(
                        request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")

            PdfCreationService.create_radicate_answer(instance, True)
        
        return redirect('pqrs:answer', pk, instance.pk)
        
    else:
        initial_values = {
            'number': radicate.number,
            'person_type' : radicate.person.person_type,
            'document_type' : radicate.person.document_type,
            'document_number' : radicate.person.document_number,
            'expedition_date_last_digit' : radicate.person.expedition_date,
            'name_company_name' : radicate.person.name,
            'lasts_name_representative' : radicate.person.lasts_name,
            'email' : radicate.person.email,
            'address' : radicate.person.address,
            'phone_number' : radicate.person.phone_number,
            'city' : radicate.person.city,
            'subject' : 'Respuesta - ' + radicate.subject,
            'observation': ''
        }
        
        if radicate.person.person_type.abbr == 'PJ':
            initial_values['name_company_name'] = radicate.person.parent.company_name
            initial_values['lasts_name_representative'] = radicate.person.parent.representative
            initial_values['expedition_date_last_digit'] = radicate.person.parent.verification_code
            initial_values['document_number'] = radicate.person.parent.document_company_number
            initial_values['document_type'] = radicate.person.parent.document_type_company
            
        form = PqrsAnswerForm(radicate, initial=initial_values)
        return render(request, 'pqrs/answer_form.html', context={'form': form, 'radicate': radicate})
    

def validate_captcha(request, pqrs):
    
    if request.is_ajax and request.method == 'POST':
        
        pqrsoparent = get_object_or_404(PQRS, uuid=pqrs)
        data = {}
        pairs = request.POST.get('data').split('&')
        for pair in pairs:
            data[pair.split('=')[0]] = pair.split('=')[1]

        form = PqrRadicateForm(pqrsoparent.pqr_type, data)
        
        if form.is_valid():
            to_json_response = dict()
            to_json_response['status'] = 1
            
            return HttpResponse(json.dumps(to_json_response), content_type='application/json')

        else:

            to_json_response = dict()
            to_json_response['status'] = 0
            to_json_response['form_errors'] = form.errors

            to_json_response['new_cptch_key'] = CaptchaStore.generate_key()
            to_json_response['new_cptch_image'] = captcha_image_url(to_json_response['new_cptch_key'])

            return HttpResponse(json.dumps(to_json_response), content_type='application/json')


def get_consultation_zip(request, pk):

    radicate = Radicate.objects.get(id=pk)
    s = io.BytesIO()
    zip_file = zipfile.ZipFile(s, 'w')
    for file in list(radicate.files.all()):
        response = ECMService.download(file.cmis_id)
        zip_file.writestr(file.name+file.extension, response[0])
    zip_file.close()
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename='+radicate.number+'.zip' 
    return resp


class AssociatedRadicateDetailView(DetailView):
    model = Radicate
    template_name="pqrs/associated_radicate_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super(AssociatedRadicateDetailView, self).get_context_data(**kwargs)
        radicate = PqrsContent.objects.get(associated_radicates=self.kwargs['pk'])
        print(radicate.__dict__)
        context['parent'] = radicate
        context['logs'] = Log.objects.all().filter(object_id=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(
            radicate=self.kwargs['pk'])
        context['files_parent'] = AlfrescoFile.objects.all().filter(
            radicate=radicate)

        return context

def change_classification(request,pk):
    pqrs_object = PqrsContent.objects.filter(pk=pk)
    print(pqrs_object)
    form  = ChangeClassificationForm()
    if request.method == "POST":
        form = ChangeClassificationForm(request.POST)
        if form.is_valid():
            
            PQRS.objects.filter(
                pk=pqrs_object[0].pqrsobject.id
                ).update(pqr_type=form['pqrs_type'].value())
            pqrs_object.update(
                subtype = form['pqrs_subtype'].value(),
                interestGroup=form['interest_group'].value()
            )


            type = Type.objects.get(pk=form['pqrs_type'].value())
            subtype = SubType.objects.get(pk=form['pqrs_subtype'].value())
            interest_group = InterestGroup.objects.get(pk=form['interest_group'].value())

            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = 'Cambio de tipo'
            action.detail = "El radicado %s ha sido modificado al tipo %s, tema %s y grupo de interés %s" %  \
                (pqrs_object[0].number, type, subtype, interest_group)
            action.radicate = pqrs_object[0]
            action.save()

            log(
                user=request.user,
                action="PQR_CHANGED",
                obj=action,
                extra={
                    "number": pqrs_object[0].number,
                    "message": "El radicado %s ha sido modificado al tipo %s, tema %s y grupo de interés %s" %  \
                            (pqrs_object[0].number, type, subtype, interest_group)
                }
            )
        return redirect('pqrs:detail_pqr', pk)
    else:
        context = {
            'form':form,
            'pqrs_object':pqrs_object[0]
        }
        return render(
            request,
            'pqrs/change_classification.html',
            context)

def bring_subtype(request):
    if request.method == "POST":
        type= request.POST['pqrs_type']
        subtype = SubType.objects.all().filter(type=type).values("name","id")
        return JsonResponse({"response":list(subtype)},status=200)
    return HttpResponse("error",status=404)
