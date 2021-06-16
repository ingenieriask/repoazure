import uuid
from django.shortcuts import redirect, render
from django.urls.base import reverse_lazy
from django.views.generic import View
from django.template.loader import render_to_string


from rest_framework import status
from rest_framework.response import Response 
from correspondence.models import ReceptionMode, RadicateTypes, Radicate, AlfrescoFile
from core.models import Attorny, AttornyType, Atttorny_Person, Person, Office, DocumentTypes, PersonRequest
from pqrs.models import PQRS,Type,PqrsContent
from pqrs.forms import SearchPersonForm, PersonForm, PqrRadicateForm,PersonRequestForm,PersonFormUpdate,PersonRequestFormUpdate,PersonAttorny
from core.utils_db import process_email,get_system_parameter
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.search import SearchVector, TrigramSimilarity, SearchQuery, SearchRank, SearchHeadline
from datetime import datetime
from django.utils.crypto import get_random_string
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
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
    rino_parameter= get_system_parameter('RINO_PQR_INFO')
    return render(request, 'pqrs/index.html', {'rino_parameter':rino_parameter.value})

def send_email_person(request, pk):
    unique_id = get_random_string(length=32)
    add_to_redis(unique_id, pk, 'email')
    person = Person.objects.get(pk=pk)
    base_url =  "{0}://{1}/pqrs/validate-email-person/{2}".format(request.scheme, request.get_host(), unique_id)
    person.url = base_url
    process_email('EMAIL_PQR_VALIDATE_PERSON', person.email, person)
    return render(request, 'pqrs/search_person_answer_form.html', context={ 'msg': 'Se ha enviado un correo electrónico con la información para registrar el caso' })

def validate_email_person(request, uuid):
    pk = read_from_redis(uuid, 'email')
    if pk is None:
        return render(request, 'pqrs/search_person_answer_form.html', context={ 'msg': 'El token ha caducado' })
    
    else:
        person = Person.objects.get(pk=pk)
        if person is None:
            return render(request, 'pqrs/search_person_answer_form.html', context={ 'msg': 'El token es inválido' })
        else:
            # url = reverse('pqrs:edit_person', kwargs={'pk': person.pk})
            url = reverse('pqrs:edit_person', kwargs={'uuid': uuid, 'pk': person.pk})
            return HttpResponseRedirect(url)

def search_person(request,pqrs_type):
    if request.method == 'POST':
        form = SearchPersonForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            qs = Person.objects.annotate(search=SearchVector('document_number', 'email', 'name'), ).filter(search=item)
            if not qs.count():
                messages.warning(request, "La búsqueda no obtuvo resultados. Registre la siguiente informacion para continuar con el proceso")
                person_form = PersonForm()
            else:
                person_form = PersonForm()
    else:
        form = SearchPersonForm()
        qs = None
        person_form = None

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form ,"pqrs_type":pqrs_type})

def create_pqr_multiple(request, pqrs):
    pqrsoparent = get_object_or_404(PQRS, uuid=pqrs)
    person = get_object_or_404(Person, id=int(pqrsoparent.principal_person.id))

    if request.method == 'POST':
        form = PqrRadicateForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.reception_mode = get_object_or_404(ReceptionMode, abbr='VIR')
            instance.type = get_object_or_404(RadicateTypes, abbr='PQR')
            instance.number = RecordCodeService.get_consecutive(1)
            instance.office = get_object_or_404(Office, abbr='PQR')
            # instance.creator = request.user.profile_user
            # instance.current_user = request.user.profile_user
            instance.person = person
            
            radicate = form.save()

            log(
                user=request.user,
                action="PQR_CREATED",
                obj=radicate,
                extra={
                    "number": radicate.number,
                    "message": "El radicado %s ha sido creado" % (radicate.number)
                }
            )
            query_url =  "{0}://{1}/correspondence/radicate/{2}".format(request.scheme, request.get_host(), radicate.pk)
            instance.url = query_url
            process_email('EMAIL_PQR_CREATE', instance.person.email, instance)

            for fileUploaded in request.FILES.getlist('uploaded_files'):
                document_temp_file = NamedTemporaryFile()
                for chunk in fileUploaded.chunks():
                    document_temp_file.write(chunk)
                    
                document_temp_file.seek(0)
                document_temp_file.flush()

                node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name))
                alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate= radicate)
                alfrescoFile.save()
            
                if not node_id or not ECMService.request_renditions(node_id):
                    messages.error(request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")


            messages.success(request, "El radicado se ha creado correctamente")
            # url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
            url = reverse('polls:show_poll', kwargs={'pk': 1})
            return HttpResponseRedirect(url)
        
        else:
            logger.error("Invalid create radicate form")
            return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person})
    else:
        form = PqrRadicateForm(initial={'person': person.id})
        form.person = person

    return render(request, 'pqrs/create_pqr.html', context={'form': form, 'person': person})


def PQRSType(request):
    pqrs_types = Type.objects.all()
    return render(request, 'pqrs/pqrs_type.html', context={'types': pqrs_types})


def multi_create_request(request,person):
    pqrs_object = get_object_or_404(PQRS, uuid=int(person))
    if request.method == 'GET':
        document_type = DocumentTypes.objects.filter(name =pqrs_object.principal_person.document_type)[0].abbr
        context ={
            'document_type_abbr':document_type,
            'person':pqrs_object.principal_person,
            'pqrs_type_option':pqrs_object.pqr_type.id,
            'pqrs_type':person,
            'other_people':pqrs_object.multi_request_person.all()}
        return render(request,'pqrs/multi_request_table.html',{'context':context})

    else:
        form = SearchPersonForm()
        qs = None
        person_form = None

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form})

def dete_person_request(request,pqrs_type,id):
    personsDelte = get_object_or_404(PersonRequest,id=id)
    personsDelte.delete()
    return redirect('pqrs:multi_request',pqrs_type)


class PqrDetailView(DetailView):
    model = Radicate
    template_name = 'pqrs/pqr_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PqrDetailView, self).get_context_data(**kwargs)
        context['logs'] = Log.objects.all().filter(object_id=self.kwargs['pk'])
        return context


# PERSONS Views
class PersonCreateView(CreateView):
    model = Person
    form_class = PersonForm
    template_name = 'pqrs/person_form.html'
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        pqrsTy = get_object_or_404(Type, id=int(self.kwargs['pqrs_type']))
        pqrsObject=PQRS(pqr_type = pqrsTy,principal_person = self.object)
        pqrsObject.save()
        if self.object.attornyCheck or form['document_type'].value()==4:
            return redirect('pqrs:create_person_attorny',pqrsObject.uuid)
        return redirect('pqrs:multi_request',pqrsObject.uuid)

class PersonRequestCreateView(CreateView):
    model = PersonRequest
    form_class = PersonRequestForm
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        pqrsObject = get_object_or_404(PQRS,uuid=self.kwargs['pqrs_type'])
        pqrsObject.multi_request_person.add(self.object)
        return redirect('pqrs:multi_request',pqrsObject.uuid)

    def get_form_kwargs(self):
        kwargs = super( PersonRequestCreateView, self).get_form_kwargs()
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
        return redirect('pqrs:multi_request',self.kwargs['pqrs_type'])

    def get_form_kwargs(self):
        kwargs = super( PersonUpdateViewNew, self).get_form_kwargs()
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
        return redirect('pqrs:multi_request',self.kwargs['pqrs_type'])

    def get_form_kwargs(self):
        kwargs = super( PersonUpdateViewNewRequest, self).get_form_kwargs()
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
        attorny_type=get_object_or_404(AttornyType,id=int(form['attorny_type'].value()))
        atornyPerson = Atttorny_Person(attorny=self.object,person=pqrsObject.principal_person,attorny_type=attorny_type)
        atornyPerson.save()
        return redirect('pqrs:multi_request',pqrsObject.uuid)
        
    def get_form_kwargs(self):
        kwargs = super( PersonAtronyCreate, self).get_form_kwargs()
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
            return render(request, 'pqrs/search_person_answer_form.html', context={ 'msg': 'El token es inválido' })
    
    
def select(requests):
    return render(requests, 'pqrs/select.html', {})


class RadicateInbox(ListView):
    model = Radicate
    context_object_name = 'radicates'
    template_name = 'pqrs/radicate_inbox.html'

    def get_queryset(self):
        queryset = super(RadicateInbox, self).get_queryset()
        queryset = queryset.filter(current_user=self.request.user.profile_user.pk)
        return queryset