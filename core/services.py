from os import name
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from .utils_services import PDF
import logging
from datetime import datetime
from django.db import transaction
import re
import requests
import json
import pandas as pd
from datetime import date, timedelta
from enum import Enum
from core.utils_db import get_system_parameter
from core.models import AppParameter, ConsecutiveFormat, Consecutive, Country, FilingType, \
    Holiday, CalendarDay, CalendarDayType, Calendar,Notifications
from core.utils import replace_data



logger = logging.getLogger(__name__)


class NotificationsHandler(object):
    '''Basic email sender'''

    _params = {}

    def send_notification(format_name, recipient_list, data):
        try:
            email_format = Notifications.objects.filter(name=format_name)
            email_format = json.loads(email_format.value)

            NotificationsHandler.send_mail(
                replace_data(email_format['subject'], data),
                replace_data(email_format['body'], data),
                'rino@skillnet.com.co',
                [recipient_list]
            )

        except Exception as Error:
            print('error de envío de correo', Error)
            logger.error(Error)

    def get_params(func):
        '''Lazy load of email database parameters'''

        def wrapper(*args, **kwargs):
            # Lazy load
            if not NotificationsHandler._params:
                # Get only email related parameters
                qs = AppParameter.objects.filter(name__startswith='EMAIL_')
                NotificationsHandler._params = {
                    entry.name: entry.value for entry in qs}
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
        code = re.sub(f'{{{cls.digits_token}}}',
                      f'{{{cls.digits_token}:0{digits}d}}', code)
        return code

    @classmethod
    def decompile(cls, code):
        '''Decompile the format for edition'''

        if not code:
            return '', 10
        digits_pattern = r'\{' + cls.digits_token + r':0(\d+)d\}'
        code = re.sub(r'\s*', r'', code)
        format = code.replace('}', '},').replace('{', ',{').replace(
            ',,', ',').strip(',')
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
        return max_response_days - cls.get_business_days_since(request_day)

    @classmethod
    def get_business_days_since(cls, request_day):
        days = CalendarDay.objects.filter(
            date__range=[request_day, date.today()])
        workingdays = 0
        if days:
            for day in days:
                workingdays += 1 if day.type.name == "workingday" else 0
            return workingdays
        
        if isinstance(request_day, datetime):
            return (date.today() - request_day.date()).days
        return (date.today() - request_day).days

    @classmethod
    def get_calendar_days(cls, year):
        return CalendarDay.objects.filter(date__year=year)

    @classmethod
    def update_calendar_days(cls, year, nonworking_days):

        nonworking_days = {date(
            *map(int, d['id'].split('T')[0].split('-'))) for d in nonworking_days if 'id' in d}
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
            days = [CalendarDay(date=d, calendar=calendar)
                    for d in day_range.date]
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
            freq=f'W-{week_day_code}',  # week_day[week_day_code],
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
            r = requests.get(
                f'{cls.holiday_api_endpoint}/{year}/{country_code}')
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
    def create_pqrs_confirmation_label(cls, pqrs):
        
        # Create pdf instance        
        pdf = PDF()
        # Add page to pdf
        pdf.add_page()
        initial_x_pos = 30.0
        initial_y_pos = 50.0
        sizing_factor = 2
        border = 0
        # Create label base in header
        pdf.custom_header(pqrs, initial_x_pos, initial_y_pos, sizing_factor, border)
        # Save pdf file
        #pdf.output('label.pdf', 'F')


    @classmethod
    def create_pqrs_summary(cls, pqrs):       
         
        # Create pdf instance    
        pdf = PDF()
        # Add page to pdf
        pdf.add_page()
        # Define left margin for the document
        pdf.set_left_margin(20.0)
        initial_x_pos = 100.0
        initial_y_pos = 12.0
        # Create custom doc header
        pdf.custom_header(pqrs, initial_x_pos, initial_y_pos, 1, 1)
        # Insert information inside doc body
        pdf.set_xy(20.0, initial_y_pos+60.0)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 5, 'CIUDAD - '+pqrs.date_radicated.strftime('%Y-%m-%d')+'\nTRATAMIENTO\n')
        pdf.set_font('Arial', 'B', 12)
        pdf.multi_cell(0, 5, 'NOMBRES DESTINATARIO\n')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 5, 'CARGO\nRAZÓN SOCIAl\nDIRECCIÓN\nEMAIL\nMUNICIPIO - DEPARTAMENTO\n\n')
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 5, 'ASUNTO: ')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0,5, pqrs.subject + '\n\n')
        pdf.multi_cell(0,5, pqrs.data + '\n\n\n\n\n\nCordialmente,\n\n\n\nDATOS DE LA PERSONA QUE FIRMA\n')
        if pqrs.pqrsobject.principal_person.is_anonymous:
            pdf.multi_cell(0,5, 'ANÓNIMO\n\n')
        else:
            pdf.multi_cell(0,5, pqrs.pqrsobject.principal_person.name+' '+pqrs.pqrsobject.principal_person.lasts_name+
                       '\nCARGO\n\n')
        pdf.set_font('Arial', '', 7)
        pdf.multi_cell(0, 5, 'Anexo (s): \n\n')
        pdf.set_font('Arial', '', 12)
        
        for annex in pqrs.files.all():
            pdf.multi_cell(0, 5, '      - ' + annex.name)
        # Create custom doc footer
        pdf.custom_footer()
        # Save pdf file
        #pdf.output('summary.pdf', 'F')
    
