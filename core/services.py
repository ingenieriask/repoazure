from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging
from datetime import datetime
from django.db import transaction
import re
import requests
import json
import pandas as pd
from datetime import date, timedelta
from enum import Enum
from fpdf import FPDF
import os

from core.models import AppParameter, ConsecutiveFormat, Consecutive, Country, FilingType, \
    Holiday, CalendarDay, CalendarDayType, Calendar

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
            email.content_subtype = "html"

            # Send email
            eb.send_messages([email])
            eb.close()
        except Exception as Error:
            logger.error(Error)

class RecordCodeService(object):

    class Type(Enum):

        INPUT = 'input'
        OUTPUT = 'output'
        MEMO = 'memo'

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
    def get_consecutive(cls, identifier):
        '''Retrieve the next consecutive code for a given type'''

        now = datetime.now()
        format = ConsecutiveFormat.objects.filter(
            effective_date__lte=now
        ).latest('effective_date').format

        filing_type = FilingType.objects.get(identifier=identifier.value)
        # Retrieve the last consecutive code
        try:
            consecutive = Consecutive.objects.get(type=filing_type)
        except Consecutive.DoesNotExist:
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
            'type': filing_type.code,
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
    def get_remaining_business_days(cls, request_day, max_response_days):
        days = CalendarDay.objects.filter(date__range=[request_day, date.today()])
        workingdays = 0
        for day in days:
            workingdays += 1 if day.type.name == "workingday" else 0
        return max_response_days - workingdays
    
    @classmethod
    def get_business_days_since(cls, request_day):
        days = CalendarDay.objects.filter(date__range=[request_day, date.today()])
        workingdays = 0
        for day in days:
            workingdays += 1 if day.type.name == "workingday" else 0
        return workingdays

    @classmethod
    def get_calendar_days(cls, year):
        return CalendarDay.objects.filter(date__year=year)

    @classmethod
    def update_calendar_days(cls, year, nonworking_days):

        nonworking_days = {date(*map(int, d['id'].split('T')[0].split('-'))) for d in nonworking_days if 'id' in d}
        days = CalendarDay.objects.filter(date__year=year)
        working_day = CalendarDayType.objects.get(name='workingday')
        nonWorking_day = CalendarDayType.objects.get(name='non-workingday')
        nonWorking_day = CalendarDayType.objects.get(name='non-workingday')
        calendar = Calendar.objects.first()
        new = not days.exists()
        if new:
            day_range = pd.date_range(
                start=f'{year}-01-01', 
                end=f'{int(year) + 1}-01-01', 
                closed='left')
            days = [CalendarDay(date=d, calendar=calendar) for d in day_range.date]
        for d in days:
            d.type = nonWorking_day if d.date in nonworking_days else working_day
        if new:
            return CalendarDay.objects.bulk_create(days)
        return CalendarDay.objects.bulk_update(days, ['type'])

    @classmethod
    def get_weekends(cls, year, week_day_code):
        '''Return the list of saturdays or sundays of an entire year'''

        return pd.date_range(
            start=f'{year}-01-01', 
            end=f'{int(year) + 1}-01-01', 
            freq=f'W-{week_day_code}', #week_day[week_day_code],
            closed='left').tolist()

    @classmethod
    def get_holidays(cls, year, country_code):
        '''Return the list of holidays for a given year and country'''

        country_code = country_code.upper()

        holidays = Holiday.objects.filter(
            date__year=year,
            country__code=country_code,
        )
        if holidays.exists():
            return holidays
        # Retrieve data from external API if not exist in local database
        try:
            r = requests.get(f'{cls.holiday_api_endpoint}/{year}/{country_code}')
            if r.ok:
                json_response = json.loads(r.text)
                country = Country.objects.get(code=country_code)
                holidays = Holiday.objects.bulk_create([Holiday(**{
                        'date': datetime.strptime(h['date'], r'%Y-%m-%d'),
                        'country': country,
                        'local_name': h['localName']
                    }) for h in json_response]
                )
                return holidays

        except Exception as Err:
            logger.error(Err)


class PdfCreationService(object):
    
    @classmethod
    def create_pqrs_pdf(cls, pqrs):
        
        annexes = pqrs.annexes if pqrs.annexes != None else '0'
        
        params = [
            ('NOMBRE DE LA DEPENDENCIA', ''),
            ('No. Radicado', pqrs.number),
            ('Fecha', pqrs.date_radicated.strftime('%Y-%m-%d %I:%M:%S %p')),
            ('Anexos', annexes)
        ]
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Courier', '', 14)
        pdf.image('static/correspondence/assets/img/favicon.png', x=20, y=20, w=30, h=30)
        for param in params:
            pdf.cell(60,40, '')
            pdf.cell(40, 10, param[0])
            pdf.cell(10, 10, '')
            pdf.cell(40, 10, param[1])
            pdf.ln(11)
            
        pdf.add_font('Barcode', '', 'static/correspondence/assets/fonts/barcode_font/BarcodeFont.ttf', uni=True)
        pdf.set_font('Barcode', '', 120)
        pdf.cell(200, 80, pqrs.number, align='C')
        #pdf.output('tuto1.pdf', 'F')
    