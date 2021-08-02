from django.http.response import JsonResponse
from django.shortcuts import render
from correspondence.models import ReceptionMode
from pqrs.models import PQRS, Type, PqrsContent,Type
from core.models import Disability, EthnicGroup, PreferencialPopulation, GenderTypes

from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
from django.db.models.functions import Lower

import logging

logger = logging.getLogger(__name__)


def calculate_statistics(request):
    if request.is_ajax():
        dates = request.GET.get('dates').split(' - ')
        selected_types = request.GET.get('selected_types')
        init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
        finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date])
        cards = []
        color_cards = ['#0080ff', 'green', 'orange', '#00cfd5', 'red', '#cccc00', '#0080ff']
        color_text = ['green', 'blue', 'black', 'grey', 'blue', '#00cfd5', 'green']
        for index, type in enumerate(list(Type.objects.filter(is_selectable=True))):
            pqrsds_count = pqrsds.filter(pqrsobject__pqr_type = type).count()
            cards.append((type.name.upper(), color_cards[index], color_text[index], pqrsds_count))
        context = {
            'pqrsds' : pqrsds,
            'cards' : cards  
        }
        
        return render(request, 'pqrs/statistics_body.html', context)

    
def calculate_horizontal_bar_chart(request):

    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'x': [], 'y': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date])
        types_query_list = Type.objects.filter(is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types)
        types_query_list = Type.objects.annotate(name_lower=Lower('name')).filter(name_lower__in = selected_types, is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
    for type in types_query_list:
        for subtype in type.subtypes.all():
            filtered_pqrsds = pqrsds.filter(subtype = subtype)
            
            response['y'].append(type.name+' / '+subtype.name)
            x_val = {
                'value' : filtered_pqrsds.count()*100/total,
                'itemStyle': {
                        'color': '#a90000'
                    }
            }
            response['x'].append(x_val)
            
    return JsonResponse(response)


def calculate_person_type_chart(request):
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'x': [], 'y': []}
    legal_pqrsds = []
    natural_pqrsds = []
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date])
        types_query_list = Type.objects.filter(is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types)
        types_query_list = Type.objects.annotate(name_lower=Lower('name')).filter(name_lower__in = selected_types, is_selectable=True)
    for type in types_query_list:
        filtered_pqrsds = pqrsds.filter(pqrsobject__pqr_type = type)
        legal_pqrsds.append(filtered_pqrsds.filter(pqrsobject__principal_person__person_type__abbr = 'PJ').count())
        natural_pqrsds.append(filtered_pqrsds.filter(pqrsobject__principal_person__person_type__abbr = 'PN').count())
        response['x'].append(type.name)
    
    natural = {
        'name': 'Natural',
        'showBackground': True,
        'type': 'bar',
        'stack': 'total',
        'label': {
            'show': True
        },
        'data': natural_pqrsds
    }
    legal = {
        'name': 'Jurídica',
        'showBackground': True,
        'type': 'bar',
        'stack': 'total',
        'itemStyle': {
            'color': '#a90000'
        },
        'label': {
            'show': True
        },
        'data': legal_pqrsds
    }
    response['y'].append(natural)
    response['y'].append(legal)
    
    return JsonResponse(response)


def calculate_state_chart(request):
    
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'x': [], 'y': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date], pqrsobject__pqr_type__is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types, pqrsobject__pqr_type__is_selectable=True)
    for status in PQRS.Status:
        response['x'].append(status.name)
        filtered_pqrsds = pqrsds.filter(pqrsobject__status = status)
        response['y'].append(filtered_pqrsds.count())
        
    return JsonResponse(response)


def calculate_disability_condition_chart(request):
    
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'data': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date], pqrsobject__pqr_type__is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types, pqrsobject__pqr_type__is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
        
    for disability in Disability.objects.all():
        filtered_pqrsds = pqrsds.filter(pqrsobject__principal_person__disabilities=disability)
        data = {
            'value': filtered_pqrsds.count()*100/total,
            'name' : disability.name
        }
        response['data'].append(data)
        
    return JsonResponse(response)


def calculate_channel_chart(request):
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'legend': [], 'x': [], 'y': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date])
        types_query_list = Type.objects.filter(is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types)
        types_query_list = Type.objects.annotate(name_lower=Lower('name')).filter(name_lower__in = selected_types, is_selectable=True)
    for type in types_query_list:
        entry = {
            'name': type.name,
            'showBackground': True,
            'type': 'bar',
            'stack': 'total',
            'label': {
                'show': True
            },
            'data': []
        }
        for reception_mode in ReceptionMode.objects.all():
            pqrsds_filtered = pqrsds.filter(pqrsobject__pqr_type=type, reception_mode=reception_mode)
            entry['data'].append(pqrsds_filtered.count())
        response['y'].append(entry)
        response['legend'].append(type.name)
    for reception_mode in ReceptionMode.objects.all():
        response['x'].append(reception_mode.name)
    
    return JsonResponse(response)


def calculate_ethnic_group_chart(request):
    
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'data': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date], pqrsobject__pqr_type__is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types, pqrsobject__pqr_type__is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
        
    for ethnic in EthnicGroup.objects.all():
        filtered_pqrsds = pqrsds.filter(pqrsobject__principal_person__ethnic_group=ethnic)
        data = {
            'value': filtered_pqrsds.count()*100/total,
            'name' : ethnic.name
        }
        response['data'].append(data)
        
    return JsonResponse(response)


def calculate_conflict_victim_chart(request):
    
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'data': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date], pqrsobject__pqr_type__is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types, pqrsobject__pqr_type__is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
        
    yes = {
        'value': pqrsds.filter(pqrsobject__principal_person__conflict_victim=True).count()*100/total,
        'name' : 'Sí'
    }    
    no = {
        'value': pqrsds.filter(pqrsobject__principal_person__conflict_victim=False).count()*100/total,
        'name' : 'No'
    }
    
    response['data'].append(yes)
    response['data'].append(no)
        
    return JsonResponse(response)


def calculate_preferential_population_chart(request):

    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'x': [], 'y': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date() 
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date])
        types_query_list = Type.objects.filter(is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types)
        types_query_list = Type.objects.annotate(name_lower=Lower('name')).filter(name_lower__in = selected_types, is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
    for population in PreferencialPopulation.objects.all():
        filtered_pqrsds = pqrsds.filter(pqrsobject__principal_person__preferencial_population = population)
        response['y'].append(population.name)
        x_val = {
            'value' : filtered_pqrsds.count()*100/total,
            'itemStyle': {
                    'color': '#a90000'
                }
        }
        response['x'].append(x_val)
            
    return JsonResponse(response)


def calculate_gender_chart(request):
    
    dates = request.GET.get('dates').split(' - ')
    selected_types = request.GET.get('selected_types')
    response = {'data': []}
    init_date = datetime.strptime(dates[0], '%B %d, %Y').date()
    finish_date = datetime.strptime(dates[1], '%B %d, %Y').date() + timedelta(days=1)
    if selected_types == '':
        pqrsds = PqrsContent.objects.filter(date_radicated__range=[init_date, finish_date], pqrsobject__pqr_type__is_selectable=True)
    else:
        selected_types = selected_types.lower().split(',')
        pqrsds = PqrsContent.objects.annotate(name_lower=Lower('pqrsobject__pqr_type__name')).filter(date_radicated__range=[init_date, finish_date],
                                            name_lower__in = selected_types, pqrsobject__pqr_type__is_selectable=True)
    if pqrsds.count() == 0:
        total = 1
    else:
        total = pqrsds.count()
        
    for gender in GenderTypes.objects.all():
        filtered_pqrsds = pqrsds.filter(pqrsobject__principal_person__gender_type=gender)
        data = {
            'value': filtered_pqrsds.count()*100/total,
            'name' : gender.name
        }
        response['data'].append(data)
        
    return JsonResponse(response)