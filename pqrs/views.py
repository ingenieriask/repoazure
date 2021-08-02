import uuid
from django.db.models import query
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from correspondence.models import Radicate, AlfrescoFile, ProcessActionStep, \
    ReceptionMode, RequestInternalInfo
from pqrs.models import PQRS, Record,Type, PqrsContent,Type, SubType, InterestGroup

from core.models import AppParameter, Atttorny_Person, LegalPerson, \
    Person, DocumentTypes, PersonRequest, PersonType, Template, ChatRooms
from django.contrib.auth.models import User
from pqrs.forms import ChangeClassificationForm, LegalPersonForm, PqrsConsultantForm, RecordsForm, SearchUniquePersonForm, PersonForm, \
    PqrRadicateForm, PqrsConsultantForm, SearchLegalersonForm, PqrsExtendRequestForm, RequestAnswerForm, \
    PqrsAnswerForm,SearchPqrsd

from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from core.utils_redis import add_to_redis, read_from_redis
from correspondence.services import RadicateService
from correspondence.ecm_services import ECMService
from core.services import DocxCreationService, HtmlPdfCreationService
from core.services import NotificationsHandler, RecordCodeService, Recipients
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from core.decorators import has_any_permission
from django.db.models import Q
from datetime import date
from core.utils_services import FormatHelper
from django.utils.http import urlencode
from django_mailbox.signals import message_received
from django.dispatch import receiver

from pinax.eventlog.models import log
from crum import get_current_user
from django.utils.decorators import method_decorator
from core.decorators import has_radicate_permission
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

import json
import io
import logging
from core.services import SystemParameterHelper, SystemHelpParameterHelper
import zipfile

logger = logging.getLogger(__name__)

@receiver(message_received)
def process_email(sender, message, **args):
    if sender.name == 'pqrs_mail':
        RadicateService.create_pqr_from_email(message)

def index(request):
    rino_parameter = SystemParameterHelper.get('RINO_PQR_INFO')
    anonymous_applicant = SystemParameterHelper.get('RINO_PQR_ANONYMOUS_APPLICANT')
    normal_applicant = SystemParameterHelper.get('RINO_PQR_NORMAL_APPLICANT')
    private_applicant = SystemParameterHelper.get('RINO_PQR_PRIVATE_APPLICANT')
    help_info = SystemHelpParameterHelper.get('pqrs:index')
    return render(
        request,
        'pqrs/index.html', {
            'rino_parameter': rino_parameter.value,
            'anonymous_applicant': anonymous_applicant.value,
            'normal_applicant': normal_applicant.value,
            'private_applicant': private_applicant.value,
            'help_info' : help_info.value
        })


def send_email_extend_request(request, instance):
    unique_id = get_random_string(length=32)
    toSave = json.dumps({
        "radicatePk": instance.pk
    })
    add_to_redis(unique_id, toSave, 'radicate')
    base_url = "{0}://{1}/pqrs/answer-request-email/{2}".format(request.scheme, request.get_host(), unique_id)
    instance.url = base_url
    if instance.person:
        NotificationsHandler.send_notification('EMAIL_PQR_EXTEND', instance, Recipients(instance.person.email, None, instance.person.phone_number))
    else:
        NotificationsHandler.send_notification('EMAIL_PQR_EXTEND', instance, Recipients(instance.email_user_email))
    

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
                                            Recipients(person.email, None, person.phone_number))
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
                    Q(document_company_number=doc_num) &
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
            radicate = RadicateService.process_pqr_creation(pqrsoparent, form, request, person)
            messages.success(request, "El radicado se ha creado correctamente")
            url = reverse('pqrs:pqrs_finish_creation', kwargs={'pk': radicate.pk})
            return HttpResponseRedirect(url)
        
        else:
            logger.error("Invalid create pqr form", form.is_valid(), form.errors)
            return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person, 'pqrs': pqrs})
    else:
        form = PqrRadicateForm(typePqr=pqrsoparent.pqr_type)
        form.person = person

    return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person, 'pqrs': pqrs})


def PQRSType(request, applicanType):
    pqrs_types = Type.objects.filter(is_selectable=True)
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
                messages.error( request, "La PQRSD no existe")
    else:
        form = PqrsConsultantForm()
    return render(
        request, 'pqrs/consultant_form.html', 
        context={
            'form': form,
            "messageHead": message_pqrs_consultant.value})

@login_required
def search_pqrsd(request):
    if request.method == 'POST':
        form = SearchPqrsd(request.POST)
        data_table =None
        if  form.is_valid():
            key_word = form.cleaned_data['key_word']
            days_before = form.cleaned_data['since']
            days_after = form.cleaned_data['until']
            limit_value = form.cleaned_data['limit_finder']
            magic_word = form.cleaned_data['search_magic_word']
            data_table = PqrsContent.objects.all().filter(
                date_radicated__range=[days_before, days_after]
            ).filter(
                Q(number=key_word) |
                Q(person__name =key_word) |
                Q(person__lasts_name=key_word) | 
                Q(person__document_number=key_word) )
            if magic_word !="None":
                data_table = data_table.filter(Q(number__contains=magic_word) | 
                Q(person__name__icontains=magic_word) | Q(subject__icontains=magic_word) | 
                Q(subtype__type__name__icontains=magic_word) | Q(subtype__name__icontains=magic_word) |
                Q(pqrsobject__status__icontains=magic_word))
            data_table = data_table[:int(limit_value)]
            if not data_table.count():
                messages.warning(
                    request, "La búsqueda no obtuvo resultados.")
    else:
        form = SearchPqrsd()
        data_table =None
    return render(
        request,
        'pqrs/pqrs_consultant.html',
        context={'form': form,"table":data_table})

@login_required
def bring_subtype(request):
    if request.method == "POST":
        type= request.POST['pqrs_type']
        subtype = SubType.objects.all().filter(type=type).values("name","id")
        return JsonResponse({"response":list(subtype)},status=200)
    return HttpResponse("error",status=404)

@login_required
def records_form(request):
    if request.method == 'POST':
        form = RecordsForm(request.POST)
        if  form.is_valid():
            record = Record(
                type = Type.objects.get(id= form['type'].value()),
                subtype =SubType.objects.get(id= form['subtype_field'].value()),
                responsable = User.objects.get(id=form['responsable'].value()),
                initial_date = form['date'].value(),
                status =  form['status'].value(),
                subject =  form['subject'].value(),
                source =  form['source'].value(),
                observations =  form['observations'].value(),
                security_levels =  form['security_levels'].value(),
            )
            record.save()

    else:
        form = RecordsForm()
    return render(
        request,
        'pqrs/records_form.html',
        context={"form":form})


@login_required
def records_form_param(request,pk):
    if request.method == 'POST':
        form = RecordsForm(pk, request.POST)
        if  form.is_valid():
            pqrs = PqrsContent.objects.get(pk=pk)
            record = Record(
                type = Type.objects.get(id= form['type'].value()),
                subtype =SubType.objects.get(id= form['subtype_field'].value()),
                responsable = User.objects.get(id=form['responsable'].value()),
                initial_date = form['date'].value(),
                status =  form['status'].value(),
                subject =  form['subject'].value(),
                source =  form['source'].value(),
                observations =  form['observations'].value(),
                security_levels =  form['security_levels'].value(),
            )
            record.name = RecordCodeService.get_proceedings_consecutive(str(record.type.pk).zfill(2) + str(record.subtype.pk).zfill(3))
            cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
            record.cmis_id = ECMService.create_folder(cmis_id, record.name)
            record.save()
            record.radicates.add(pqrs)
            ECMService.copy_item(pqrs.folder_id, record.cmis_id)
            for radicate in pqrs.associated_radicates.all():
                record.radicates.add(radicate)
                ECMService.copy_item(radicate.folder_id, record.cmis_id)
            record.save()
            return redirect('pqrs:detail_pqr', pk)
    else:
        form = RecordsForm(pk)
    return render(
        request,
        'pqrs/records_form.html',
        context={"form":form,"pk":pk})

def create_room(request):
    if request.method == 'POST':
        data = request.POST
        new_room = ChatRooms(
            name_room=data['name_room'],
            reference_name_creator=data['reference_name_creator'],
            email=data['email_room']
        )
        new_room.save()
        return HttpResponse(new_room.code_room)
    return HttpResponse(False)
    
class RecordDetailView(DetailView):
    model = Record

class RecordListView(ListView):
    model = Record
    context_object_name = 'records'

class PqrDetailView(DetailView):
    model = Radicate
    template_name = 'pqrs/pqr_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
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

class RadicateListView(ListView):
    paginate_by = 5

    def get_paginate_by(self, queryset):
        return self.request.GET.get("paginate_by", self.paginate_by)

    
    def filter(func):

        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            term = args[0].request.GET.get('filter', None)
            if term == 'None':
                term = None
            if term:
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
        queryset = queryset.filter(is_filed=False, subtype__isnull=False, pqrsobject__status=PQRS.Status.CREATED)
        return queryset

#@method_decorator(login_required, name='dispatch')
@method_decorator(has_any_permission(['auth.receive_external']), name='dispatch')
class RadicateEmailInbox(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_email_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateEmailInbox, self).get_queryset()
        queryset = queryset.filter(is_filed=False, subtype__isnull=False, pqrsobject__status=PQRS.Status.EMAIL)
        return queryset

class RadicateMyInbox(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_my_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateMyInbox, self).get_queryset()
        queryset = queryset.filter(is_filed=False, current_user = self.request.user, subtype__isnull=False, stage=Radicate.Stage.IN_PROCESS)
        return queryset

class RadicateMyReported(RadicateListView):
    model = PqrsContent
    context_object_name = 'pqrs'
    template_name = 'pqrs/radicate_reported_inbox.html'

    @RadicateListView.filter
    def get_queryset(self):
        queryset = super(RadicateMyReported, self).get_queryset()
        queryset = queryset.filter(is_filed=False, reported_people = self.request.user, subtype__isnull=False)
        return queryset

@method_decorator(has_radicate_permission([]), name='dispatch')
class PqrDetailProcessView(DetailView):
    model = PqrsContent
    template_name = 'pqrs/pqr_detail_process_actions.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailProcessView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        if context['pqrscontent'].person and context['pqrscontent'].person and context['pqrscontent'].person.attornyCheck:
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
        if context['pqrscontent'].person and context['pqrscontent'].person.attornyCheck:
            personAttorny = Atttorny_Person.objects.filter(person=context['pqrscontent'].person.pk)[0]
            context['personAttorny'] = personAttorny
        return context

@method_decorator(has_radicate_permission([]), name='dispatch')
class PqrDetailEmailView(DetailView):
    model = PqrsContent
    template_name = 'pqrs/pqr_detail_process_actions_email.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailEmailView, self).get_context_data(**kwargs)
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        if context['pqrscontent'].person and context['pqrscontent'].person.attornyCheck:
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
        if context['pqrscontent'].person and context['pqrscontent'].person.attornyCheck:
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
    
    elif 'id' in request.GET:
        obj = RequestInternalInfo.objects.get(id=request.GET['id']) 
        obj.date_radicated = obj.radicate.date_radicated.strftime("%d/%m/%y")
        obj.date_creation = obj.date_creation.strftime("%d/%m/%y")
        obj.status_str = str(obj.get_status_str())
        obj.number = obj.radicate.number
        
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
        context['answers'] = Radicate.objects.filter(mother=context['pqrs'].id, 
                                                     classification=Radicate.Classification.COMPLETE_ANSWER)
        return context

def pqrs_extend_request(request, pk):
    
    radicate = PqrsContent.objects.get(pk=pk) #get_object_or_404(PqrsContent, id=pk)
    print(request.method)

    if request.method == 'POST':
        
        form = PqrsExtendRequestForm(radicate, request.POST)
        print(form.is_valid(), form.errors)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.number = RecordCodeService.get_consecutive(RecordCodeService.Type.OUTPUT)
            instance.type = radicate.type
            instance.record = radicate.record
            instance.person = radicate.person
            if not instance.person:
                instance.email_user_email = request.POST['email']
                instance.email_user_name = request.POST['name_company_name']
            instance.reception_mode = radicate.reception_mode
            instance.office = radicate.office
            instance.doctype = radicate.doctype
            instance.parent = radicate
            instance.classification = Radicate.Classification.AMPLIATION_REQUEST
            
            instance.save()
            cmis_id = AppParameter.objects.get(name = 'ECM_TEMP_FOLDER_ID').value
            folder_id = ECMService.create_folder(cmis_id, instance.number)
            instance.folder_id = folder_id
            instance.save()

            instance.date_radicated_formated = radicate.date_radicated.strftime('%Y-%m-%d')
            instance.original_number = radicate.number
            send_email_extend_request(request, instance)
            RadicateService.process_files(request.FILES.getlist('uploaded_files'), instance, request)
            HtmlPdfCreationService.generate_pdf(Template.Types.PQR_EXT_REQUEST, instance.data, instance)

            RadicateService.add_to_record(instance.parent, instance)
            RadicateService.create_action_creation(instance)

            ## log de solicitud de ampliación de información del radicado original
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = ProcessActionStep.ActionTypes.AMPLIATION_REQUEST
            action.detail = 'Se ha solicitado ampliación de información al radicado %s' % (instance.parent.number) 
            action.radicate = instance.parent
            action.save()

            messages.success(request, "La solicitud de ampliación se ha creado correctamente")
            return redirect('pqrs:detail_pqr', pk)
        else:
            logger.error(form.errors)
        return HttpResponseRedirect(request.path_info)
    else:
        formatted_data = Template.objects.get(type=Template.Types.PQR_EXT_REQUEST).file.read().decode("utf-8") 
        formatted_data = FormatHelper.replace_data_preparing_html(formatted_data, radicate)
        initial_values = {
            'number': radicate.number,
            'person_type' : radicate.person.person_type if radicate.person else None,
            'document_type' : radicate.person.document_type if radicate.person else None,
            'document_number' : radicate.person.document_number if radicate.person else None,
            'expedition_date_last_digit' : radicate.person.expedition_date if radicate.person else None,
            'name_company_name' : radicate.person.name if radicate.person else radicate.email_user_name,
            'lasts_name_representative' : radicate.person.lasts_name if radicate.person else None,
            'email' : radicate.person.email if radicate.person else radicate.email_user_email,
            'address' : radicate.person.address if radicate.person else None,
            'phone_number' : radicate.person.phone_number if radicate.person else None,
            'city' : radicate.person.city if radicate.person else None,
            'subject' : 'Ampliación de solicitud - ' + radicate.subject,
            'data': formatted_data
        }
        
        if radicate.person and radicate.person.person_type.abbr == 'PJ':
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
                instance = PqrsContent.objects.get(number = number)
                instance.parent = radicate
                instance.pqrsobject.status = PQRS.Status.ANSWERED
                instance.classification = classification
                instance.stage = Radicate.Stage.CLOSED
                instance.pqrsobject.save()
                instance.save()

                action = ProcessActionStep()
                action.user = get_current_user()
                action.action = ProcessActionStep.ActionTypes.ASSOCIATION
                action.detail = 'El radicado %s ha sido asociado al radicado %s' % (instance.number, instance.parent.number) 
                action.radicate = instance
                action.save()

                ### creation of the authomatic answer
                ans = SystemParameterHelper.get_json('ANSWER_ASSOCIATION')
                answer_pqr = Radicate()
                RadicateService.fill_from_parent(answer_pqr, instance)
                answer_pqr.subject = ans['subject']
                answer_pqr.data = FormatHelper.replace_data(ans['data'], answer_pqr)
                RadicateService.answer_radicate(answer_pqr, instance, request)

                RadicateService.add_to_record(instance.parent, instance)
                RadicateService.add_to_record(answer_pqr.parent, answer_pqr)

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
                action.action = ProcessActionStep.ActionTypes.ASSOCIATION
                action.detail = 'El radicado %s ha sido asociado al radicado %s' % (instance.number, radicate.number) 
                action.radicate = instance.parent
                action.save()

                messages.success(request, "La solicitud de asociación se ha procesado correctamente")
                return redirect('pqrs:detail_pqr', pk)
            except Exception as Error:
                print(Error)
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
            instance.number = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
            instance.type = radicate.type
            instance.record = radicate.record
            instance.person = radicate.person
            instance.email_user_email = radicate.email_user_email
            instance.email_user_name = radicate.email_user_name
            instance.reception_mode = radicate.reception_mode
            instance.office = radicate.office
            instance.doctype = radicate.doctype
            instance.parent = radicate.parent
            instance.classification = Radicate.Classification.AMPLIATION_ANSWER
            
            instance.save()
            cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
            folder_id = ECMService.create_folder(cmis_id, instance.number)
            instance.folder_id = folder_id
            instance.save()

            
            DocxCreationService.mix_from_template(Template.Types.PQR_EXT_ANSWER, instance)

            RadicateService.process_files(request.FILES.getlist('uploaded_files'), instance, request)
            RadicateService.add_to_record(instance.parent, instance)
            
            RadicateService.create_action_creation(instance)

            ## log de respuesta del radicado de solicitud de ampliación de información
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = ProcessActionStep.ActionTypes.ANSWER
            action.detail = 'El radicado %s ha sido respondido' % (radicate.number) 
            action.radicate = radicate
            action.save()

            ## log de respuesta del radicado original de la solicitud de ampliación de información
            action = ProcessActionStep()
            action.user = get_current_user()
            action.action = ProcessActionStep.ActionTypes.ANSWER
            action.detail = 'El radicado %s ha sido respondido' % (radicate.number) 
            action.radicate = instance.parent
            action.save()

            get_args_str = urlencode({'template': 'PROCEDURE_CONCLUSION', 'destination': 'index'})
            return HttpResponseRedirect(reverse('pqrs:conclusion')+'?'+get_args_str)
            
        return HttpResponseRedirect(request.path_info)
                
    else:
        
        form = RequestAnswerForm(initial={'number' : radicate.number, 'question': radicate.data})
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
        RadicateService.answer_radicate(radicate, radicate.parent, request)
        messages.success(request, "El radicado se ha creado correctamente")
        return redirect('pqrs:detail_pqr', pk)
    else:
        cmis = AlfrescoFile.objects.get(radicate=actualPk, name = radicate.number)
        return render(request, 'pqrs/answer_radicate_form.html', context={'radicate': radicate, 'cmis': cmis.cmis_id})

def pqrs_answer_preview(request, pk):
    
    radicate = get_object_or_404(PqrsContent, id=pk)

    if request.method == 'POST':
        
        form = PqrsAnswerForm(radicate, request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            RadicateService.fill_from_parent(instance, radicate)
            ### se crea un identificador de folder temporal
            instance.folder_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
            instance.save()

            RadicateService.process_files(request.FILES.getlist('answer_uploaded_files'), instance, request)
            
            DocxCreationService.mix_from_template(Template.Types.PQR_CREATION, instance)
            return redirect('pqrs:answer', pk, instance.pk)
        else:
            print(form.errors)
        
    else:
        initial_values = {
            'number': radicate.number,
            'person_type' : radicate.person.person_type if radicate.person else None,
            'document_type' : radicate.person.document_type if radicate.person else None,
            'document_number' : radicate.person.document_number if radicate.person else None,
            'expedition_date_last_digit' : radicate.person.expedition_date if radicate.person else None,
            'name_company_name' : radicate.person.name if radicate.person else radicate.email_user_name,
            'lasts_name_representative' : radicate.person.lasts_name if radicate.person else None,
            'email' : radicate.person.email if radicate.person else radicate.email_user_email,
            'address' : radicate.person.address if radicate.person else None,
            'phone_number' : radicate.person.phone_number if radicate.person else None,
            'city' : radicate.person.city if radicate.person else None,
            'subject' : 'Respuesta - ' + radicate.subject,
            'data': ''
        }
        
        if radicate.person and radicate.person.person_type.abbr == 'PJ':
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
        context['parent'] = radicate
        context['logs'] = ProcessActionStep.objects.all().filter(radicate=self.kwargs['pk'])
        context['files'] = AlfrescoFile.objects.all().filter(radicate=self.kwargs['pk'])
        context['files_parent'] = AlfrescoFile.objects.all().filter(radicate=radicate)

        return context

def change_classification(request,pk):
    pqrs_object = PqrsContent.objects.get(pk=pk)
    form  = ChangeClassificationForm()

    if request.method == "POST":
        create = pqrs_object.pqrsobject.status == PQRS.Status.EMAIL
        form = ChangeClassificationForm(request.POST)
        if form.is_valid():
            type = Type.objects.get(pk=form['pqrs_type'].value())
            subtype = SubType.objects.get(pk=form['pqrs_subtype'].value())
            interest_group = InterestGroup.objects.get(pk=form['interest_group'].value())
            
            pqrs_object.pqrsobject.pqr_type=type
            pqrs_object.pqrsobject.status = PQRS.Status.CREATED
            pqrs_object.subtype = subtype
            pqrs_object.interestGroup = interest_group

            if create:
                pqrs_object.number = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
                cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
                pqrs_object.folder_id = ECMService.create_folder(cmis_id, pqrs_object.number)
                pqrs_object.stage = Radicate.Stage.IN_PROCESS

                for file in AlfrescoFile.objects.filter(radicate=pqrs_object):
                    ECMService.move_item(file.cmis_id, pqrs_object.folder_id)

                RadicateService.create_action_creation(pqrs_object)
            pqrs_object.pqrsobject.save()
            pqrs_object.save()

            if create:
                query_url = "{0}://{1}/pqrs/consultation/result/{2}".format(request.scheme, request.get_host(), pqrs_object.pk)
                pqrs_object.url = query_url
                formatted_data = Template.objects.get(type=Template.Types.PQR_CREATION).file.read().decode("utf-8") 
                formatted_data = FormatHelper.replace_data_preparing_html(formatted_data, pqrs_object)
                pqrs_object.data = formatted_data
                pqrs_object.save()
                NotificationsHandler.send_notification('EMAIL_PQR_CREATE', pqrs_object, Recipients(pqrs_object.email_user_email))
                HtmlPdfCreationService.generate_pdf(Template.Types.PQR_CREATION, pqrs_object.data, pqrs_object)
                RadicateService.process_next_action(pqrs_object)
                RadicateService.create_record(pqrs_object)

            else:
                action = ProcessActionStep()
                action.user = get_current_user()
                action.action = ProcessActionStep.ActionTypes.CHANGE_TYPE
                action.detail = "El radicado %s ha sido modificado al tipo %s, tema %s y grupo de interés %s" %  \
                    (pqrs_object.number, type, subtype, interest_group)
                action.radicate = pqrs_object
                action.save()

            log(
                user=request.user,
                action="PQR_CHANGED",
                obj=action,
                extra={
                    "number": pqrs_object.number,
                    "message": "El radicado %s ha sido modificado al tipo %s, tema %s y grupo de interés %s" %  \
                            (pqrs_object.number, type, subtype, interest_group)
                }
            )
            if create:
                return redirect('pqrs:radicate_email_inbox')
            else:
                return redirect('pqrs:detail_pqr', pk)
    else:
        context = {
            'form':form,
            'pqrs_object':pqrs_object
        }
        return render(
            request,
            'pqrs/change_classification.html',
            context)


class PqrsStatistics(ListView):
    model = PqrsContent
    template_name = 'pqrs/statistics.html'
    