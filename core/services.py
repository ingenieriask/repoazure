from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging
from datetime import datetime
from django.db import transaction
import re
import requests
import json
import pandas as pd
from datetime import date

from core.models import AppParameter, ConsecutiveFormat, Consecutive, Country, FilingType, \
    Holiday

logger = logging.getLogger(__name__)

class MailService(object):
    '''Basic email sender'''

    _params = {}

    def get_params(func):
        '''Lazy load of email database parameters'''
    
        def wrapper(*args, **kwargs):
            # Lazy load
            if not MailService._params:
                # Get only email related parameters
                qs = AppParameter.objects.filter(name__startswith='EMAIL_')
                MailService._params = {entry.name : entry.value for entry in qs}
            return func(*args, **kwargs)
        return wrapper

    @classmethod
    @get_params
    def send_mail(cls, subject='', body='', from_email=None, to=None):
        '''Send emails to several addresses using database parameters'''

        if not from_email:
            from_email = cls._params['EMAIL_HOST_USER']

        # Configure email handler
        eb = EmailBackend(
            host=cls._params['EMAIL_HOST'], 
            port=int(cls._params['EMAIL_PORT']), 
            username=cls._params['EMAIL_HOST_USER'], 
            password=cls._params['EMAIL_HOST_PASSWORD'], 
            use_tls=bool(cls._params['EMAIL_USE_TLS']), 
            fail_silently=False)
        try:
            eb.open()
            email = EmailMessage(subject, body, from_email, to)

            # Send email
            eb.send_messages([email])
            eb.close()
        except Exception as Error:
            logger.error(Error)

class RecordCodeService(object):

    tokens = ['{consecutive}', '{year}', '{type}']
    digits_token = 'consecutive'

    @classmethod
    def compile(cls, format, digits):
        '''Generate format from edited data'''

        code = re.sub(r'\s*', r'', format)
        code = re.sub(r',', r'', code)
        code = re.sub(f'{{{cls.digits_token}}}', f'{{{cls.digits_token}:0{digits}d}}', code)
        return code

    @classmethod
    def decompile(cls, code):
        '''Decompile the format for edition'''

        if not code:
            return '', 10
        digits_pattern = r'\{' + cls.digits_token + r':0(\d+)d\}'
        code = re.sub(r'\s*', r'', code)
        format = code.replace('}', '},').replace('{', ',{').replace(',,', ',').strip(',')
        format = re.sub(digits_pattern, f'{{{cls.digits_token}}}', format)
        r = re.search(digits_pattern, code)
        digits = int(r.group(1)) if r else 0
        return format, digits

    @classmethod
    @transaction.atomic
    def get_consecutive(cls, type):
        '''Retrieve the next consecutive code for a given type'''

        now = datetime.now()
        format = ConsecutiveFormat.objects.filter(
            effective_date__lte=now
        ).latest('effective_date').format

        # Retrieve the last consecutive code
        try:
            consecutive = Consecutive.objects.get(type__code=type)
        except Consecutive.DoesNotExist:
            filing_type = FilingType.objects.get(code=type)
            consecutive = Consecutive(current=0, type=filing_type)

        # Update the consecutive code
        if consecutive.date.year != now.year:
            consecutive.current = 1
        else:
            consecutive.current += 1

        consecutive.date = now
        consecutive.save()
        
        # Generate formatted code
        params = {
            'type': type,
            'year': now.year,
            'consecutive': consecutive.current
        }

        return format.format(**params)

class CalendarService(object):
    '''Service for calculate working days'''

    # https://date.nager.at/
    # API limitations:
    # 50 requests per day
    holiday_api_endpoint = 'https://date.nager.at/api/v3/publicholidays'
    
    @classmethod
    def get_days_of_year():
        return 

    @classmethod
    def get_weekends(cls, year, week_day_code):

        week_day = {'SAT': 'W-SUN', 'SUN': 'W-MON'}

        '''Return the list of saturdays or sundays of an entire year'''
        return pd.date_range(
            start=f'{year}-01-01', 
            end=f'{int(year) + 1}-01-01', 
            freq=week_day[week_day_code],
            closed='left').strftime(r'%Y-%m-%d').tolist()

    @classmethod
    def get_holidays(cls, year, country_code):
        '''Return the list of holidays for a given year and country'''

        country_code = country_code.upper()

        holidays = Holiday.objects.filter(
            date__year= year,
            country__code=country_code,
        )
        if holidays.exists():
            print('from local db')
            return holidays
        # Retrieve data from external API if not exist in local database
        try:
            r = requests.get(f'{cls.holiday_api_endpoint}/{year}/{country_code}')
            if r.ok:
                json_response = json.loads(r.text)
                country = Country.objects.get(code=country_code)
                holidays = Holiday.objects.bulk_create([Holiday(**{
                        'date': h['date'],
                        'country': country,
                        'local_name': h['localName']
                    }) for h in json_response]
                )
                return holidays

        except Exception as Err:
            logger.error(Err)
