from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from datetime import datetime
from core.services import CalendarService

def holidays(request):
    '''Return the list of holidays for a given year and country'''

    # request should be ajax and method should be GET.
    if request.is_ajax and request.method == "GET":  
    
        year = request.GET.get('year', datetime.now().year)
        country = request.GET.get('country', 'CO')
        holidays = [{
            'date': h.date,
            'country': h.country.code,
            'local_name': h.local_name
            } for h in CalendarService.get_holidays(year, country)]
        return JsonResponse(holidays, safe=False, status=200)

    return JsonResponse({}, status=400)

def weekends(request):
    '''Return the list of saturdays or sundays of an entire year'''

    # request should be ajax and method should be GET.
    if request.is_ajax and request.method == "GET":  
    
        year = request.GET.get('year', datetime.now().year)
        day = request.GET.get('day', 'SAT').upper()

        # only saturdays or sundays are valid
        if day in ('SAT', 'SUN'):   
            CalendarService.get_weekends(year, day)

            holidays = [{
                'date': h,
                } for h in CalendarService.get_weekends(year, day)]
            return JsonResponse(holidays, safe=False, status=200)

    return JsonResponse({}, status=400)