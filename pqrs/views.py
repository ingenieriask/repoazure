from django.shortcuts import redirect, render
from django.urls.base import reverse_lazy
from django.views.generic import View
from django.template.loader import render_to_string

from rest_framework import status
from rest_framework.response import Response 
from correspondence.models import ReceptionMode, RadicateTypes, Radicate
from core.models import Person, Office, DocumentTypes, Poll, PollInstance,PersonRequest
from pqrs.models import PQR,Type
from pqrs.forms import SearchPersonForm, PersonForm, PqrRadicateForm,PersonRequestForm,PersonFormUpdate,PersonRequestFormUpdate
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
    base_url =  "{0}://{1}/pqrs/validate_email_person/{2}".format(request.scheme, request.get_host(), unique_id)
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
            url = reverse('pqrs:edit_person', kwargs={'pk': person.pk, 'uuid': uuid})
            return HttpResponseRedirect(url)

def search_person(request):
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

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form})

def create_pqr(request, person):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    person = get_object_or_404(Person, id=person)

    if request.method == 'POST':
        form = PqrRadicateForm(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            cleaned_data = form.cleaned_data
            form.document_file = request.FILES['document_file']
            now = datetime.now()
            instance.number = now.strftime("%Y%m%d%H%M%S")
            instance.reception_mode = get_object_or_404(ReceptionMode, abbr='VIR')
            instance.type = get_object_or_404(RadicateTypes, abbr='PQR')
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

            process_email('EMAIL_PQR_CREATE', instance.person.email, instance)

            files = open(os.path.join(BASE_DIR, radicate.document_file.path), "rb")

            node_id = ECMService.upload(files)

            if node_id:
                radicate.set_cmis_id(node_id)

                if ECMService.request_renditions(node_id):
                    messages.success(request, "El radicado se ha creado correctamente")
                    url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
                    return HttpResponseRedirect(url)

                messages.error(request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")
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
    personsarray =str(person).split('&')
    personInstance = get_object_or_404(Person, id=int(personsarray[0]))
    if request.method == 'GET':
        document_type = DocumentTypes.objects.filter(name =personInstance.document_type)[0].abbr
        argsReturn= "".join([str(elem)+'&' for elem in personsarray])[:-1]
        if len(personsarray)>1:
            argumentss = personsarray[1:]
            other_people = argumentss
            objects_person_request = [ PersonRequest.objects.filter(id=int(i))[0] for i in other_people]     
            context ={'document_type_abbr':document_type , 'person':personInstance,'args':argsReturn,'other_people':objects_person_request}
        else:
            context ={'document_type_abbr':document_type , 'person':personInstance,'args':argsReturn}
        return render(request,'pqrs/multi_request_table.html',{'context':context})

    else:
        form = SearchPersonForm()
        qs = None
        person_form = None

    return render(request, 'pqrs/search_person_form.html', context={'form': form, 'list': qs, 'person_form': person_form})
    


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

class PersonRequestCreateView(CreateView):
    model = PersonRequest
    form_class = PersonRequestForm
    template_name = 'pqrs/person_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        person = str(self.kwargs['arguments'])+'&'+str(self.object.id)
        return redirect('/pqrs/multi-request/'+str(person)+'/')  

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
        return redirect('/pqrs/multi-request/'+str(self.kwargs['arguments'])+'/')  

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
        return redirect('/pqrs/multi-request/'+str(self.kwargs['arguments'])+'/')  

    def get_form_kwargs(self):
        kwargs = super( PersonUpdateViewNewRequest, self).get_form_kwargs()
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


def show_poll(request, pk):
    
    try:
        poll = Poll.objects.get(id=pk)
    except:
        messages.error(request, "Poll does not exists!")
        return render(request, 'pqrs/show_poll.html')

    if request.method=='POST':
        
        arr = []
        for elem in request.POST.items():
            arr.append(elem[1])
        
        arr = arr[1:]
        PollInstance(poll = poll, answers = arr).save()
        
    return render(request, 'pqrs/show_poll.html', {'poll': poll})