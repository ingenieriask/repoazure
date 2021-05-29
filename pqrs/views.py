from django.shortcuts import render
from django.views.generic import View

from correspondence.models import ReceptionMode, RadicateTypes, Radicate
from core.models import Person, Office
from pqrs.models import PQR
from pqrs.forms import SearchPersonForm, PersonForm, PqrRadicateForm
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
                messages.warning(request, "La búsqueda no obtuvo resultados")
                person_form = None
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


class PersonDetailView(DetailView):
    model = Person

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
