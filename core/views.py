from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import BadHeaderError, send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from core.services import CalendarService, MailService

def holidays(request):
    '''Return the list of holidays for a given year and country'''

    # request should be ajax and method should be GET.
    if request.is_ajax and request.method == "GET":  
    
        year = request.GET.get('year', datetime.now().year)
        country = request.GET.get('country', 'CO')
        holidays = [{
            'date': h.date.strftime(r'%Y-%m-%dT00:00:00'),
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
            holidays = [{
                'date': w.strftime(r'%Y-%m-%dT00:00:00'),
                } for w in CalendarService.get_weekends(year, day)]
            return JsonResponse(holidays, safe=False, status=200)

    return JsonResponse({}, status=400)

def not_working_days(request):
    '''Return the list of configurated days of an entire year'''

    # request should be ajax and method should be GET.
    if request.is_ajax and request.method == "GET":  
        year = request.GET.get('year', datetime.now().year)
        formatted_days = [{
            'date': d.date.strftime(r'%Y-%m-%dT00:00:00'), 
            'type': d.type.name
            } for d in CalendarService.get_calendar_days(year) if d.type.name != 'workingday'],
        return JsonResponse(formatted_days, safe=False, status=200)

    return JsonResponse({}, status=400)

def password_reset_request(request):
    if request.method == "POST":
        domain = request.headers['Host']
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))

            if associated_users.exists():
                for user in associated_users:
                    subject = "Solicitud de restablecimiento de contraseña"
                    email_template_name = "registration/password_reset_email.html"
                    c = {
                        "email": user.email,
                        'domain': domain,
                        'site_name': 'Interface',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        MailService.send_mail(subject, email, to=[user.email])
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect('password_reset_done') #"/core/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="registration/password_reset.html",
                  context={"password_reset_form": password_reset_form})