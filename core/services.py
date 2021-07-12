from os import name
from typing import Type
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
from django.core.exceptions import ValidationError
from core.models import AppParameter, ConsecutiveFormat, Consecutive, Country, FilingType, \
    Holiday, CalendarDay, CalendarDayType, Calendar, Notifications, SystemParameter
from core.utils_services import FormatHelper
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class SystemParameterHelper():
    ''' '''
    
    @classmethod
    def get(cls, format_name):
        return SystemParameter.objects.get(name=format_name)

    @classmethod
    def get_json(cls, format_name):
        return json.loads(cls.get(format_name).value)

class Recipients():

    def __init__(self, email_to, email_cc=None, phone_to=None):

        self.email_to = [email_to] if isinstance(email_to, str) else email_to
        if email_cc:
            self.email_cc = [email_cc] if isinstance(email_cc, str) else email_cc
        else:
            self.email_cc = None
        if phone_to:
            self.phone_to = [phone_to] if isinstance(phone_to, str) else phone_to
        else:
            self.phone_to = None

class NotificationsHandler(object):
    '''Notification sender'''

    _params = {}

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

    _services = {
        'SEND_EMAIL': lambda data, email_format, recipients: NotificationsHandler.send_mail(
                    FormatHelper.replace_data(email_format.subject, data),
                    FormatHelper.replace_data(email_format.body, data),
                    NotificationsHandler._params['EMAIL_HOST_USER'],
                    recipients.email_to,
                    recipients.email_cc if recipients.email_cc else None
                ),
        'SEND_SMS': None
    }

    @classmethod
    @get_params
    def send_notification(cls, format_name, data, recipients):
        try:
            email_format = Notifications.objects.get(name=format_name)

            for service in email_format.notifications_services.all():
                if service.name in cls._services:
                    if cls._services[service.name]:
                        cls._services[service.name](data, email_format, recipients)
                    else:
                        logger.error(f"service '{service}' unimplemented")
                else:
                    logger.error(f"service '{service}' undefined")

        except Exception as Error:
            print(f'Notification sending error: {Error}')
            logger.error(f'Notification sending error: {Error}')

    @classmethod
    @get_params
    def send_mail(cls, subject='', body='', from_email=None, to=None, cc=None):
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
            email = EmailMessage(subject, body, from_email, to, cc)
            email.content_subtype = "html"

            # Send email
            eb.send_messages([email])
            eb.close()
        except Exception as Error:
            logger.error('Error enviando el correo', Error)


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
        
        annexes = ''
        for index, val in enumerate(list(radicate.files.all())):
            annexes += val.name
            if index != len(list(radicate.files.all())) - 1:
                annexes += ', '
        
        pdf.multi_cell(0, 5, 'Anexo (s): ' + annexes)
        
        # Create custom doc footer
        pdf.custom_footer()
        # Save pdf file
        #pdf.output('summary.pdf', 'F')
    
    @classmethod
    def create_radicate_answer(cls, radicate, draft):
        # Create pdf instance    
        pdf = PDF()
        # Add page to pdf
        pdf.add_page()
        #add watermark if the document is a draft
        if draft:
            pdf.image('static/pqrs/img/draft_watermark.png', w=200, h=260)
        # Define left margin for the document
        pdf.set_left_margin(20.0)
        pdf.set_right_margin(-20.0)
        initial_x_pos = 100.0
        initial_y_pos = 12.0
        # Create custom doc header
        pdf.custom_header(radicate, initial_x_pos, initial_y_pos, 1, 1)
        # Insert information inside doc body
        pdf.set_xy(20.0, initial_y_pos+60.0)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 5, 'CIUDAD - '+ radicate.date_radicated.strftime('%Y-%m-%d')+'\n\nSeñor(a)\n')
        pdf.set_font('Arial', 'B', 12)
        if radicate.person.person_type.abbr == "PJ":
            pdf.multi_cell(0, 5, radicate.person.parent.representative+'\n')
        else:
            pdf.multi_cell(0, 5, radicate.person.name+' '+radicate.person.lasts_name+'\n')
        pdf.set_font('Arial', '', 12)
        if radicate.person.address:
            pdf.multi_cell(0, 5, radicate.person.address+'\n'+radicete.person.email+'\n'+radicate.person.city.name+' '+radicate.person.city.state.name+'\n\n')
        else:
            pdf.multi_cell(0, 5, '\n'+radicate.person.email+'\n'+radicate.person.city.name+' '+radicate.person.city.state.name+'\n\n')
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(20, 5, 'ASUNTO: ')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0,5, radicate.subject + '\n\n')
        pdf.multi_cell(0,5, radicate.observation + '\n\n\n\n\n\nCordialmente,\n\n\n\nRINO GESTIÓN DOCUMENTAL'+
                       '\nJosé Gonzáles\nGerente\n\n')
        pdf.set_font('Arial', '', 7)
        
        annexes = ''
        for index, val in enumerate(list(radicate.files.all())):
            annexes += val.name
            if index != len(list(radicate.files.all())) - 1:
                annexes += ', '
        
        pdf.multi_cell(0, 5, 'Anexo (s): ' + annexes)
        
        # Create custom doc footer
        pdf.custom_footer()
        # Define total number of pages
        pdf.alias_nb_pages()
        # Save pdf file
        #pdf.output('answer.pdf', 'F')

class SignatureFlowService(object):

    class Type(Enum):
        INPUT = 'Inicio'
        OUTPUT = 'Fin'
        GUARANTORUSER = 'Avalador'
        SIGNINGUSER = 'Firmante'

    @classmethod
    def to_json(cls, pk):
        end_node = SignatureNode.objects.filter(signature_flow__id=pk, type=cls.Type.OUTPUT.value).first()
        if end_node:
            formated_nodes = {}
            cls._format_node(end_node, formated_nodes)
            return {
                "id": "demo@0.1.0",
                "nodes": formated_nodes
            }
        return cls.get_initial_json()

    @classmethod
    def _append_output(cls, outputs, next_node):
        if next_node:
            outputs['out']['connections'].append(
                {
                    "node": next_node,
                    "input": "in",
                    "data": {}
                }
            )

    @classmethod
    def _format_node(cls, node, formated_nodes, next_node=None):
        if node.index in formated_nodes:
            cls._append_output(formated_nodes[node.index]['outputs'], next_node)
        else:
            outputs = {
                "out": {
                    "connections": []
                }
            }
            cls._append_output(outputs, next_node)
            properties = json.loads(node.properties)
            previous_nodes = node.previous.all()
            inputs = {}
            if previous_nodes:
                inputs = {
                    "in": {
                        "connections": [
                            {
                                "node": n.index,
                                "output": "out",
                            }
                            for n in previous_nodes
                        ]
                    }
                }
            formated_node = {
                'id': node.index,
                'data': {
                    'user_id': node.user.id if node.user else None
                },
                'inputs': inputs,
                'outputs': outputs,
                **properties,
                'name': node.type
            }
            formated_nodes[node.index] = formated_node

            for previous_node in previous_nodes:
                cls._format_node(previous_node, formated_nodes, node.index)

        return 

    @classmethod
    def from_json(cls, graph, signature_flow_id):

        nodes = {}
        node_list = []

        acc = {
            SignatureFlowService.Type.SIGNINGUSER.value: 0,
            SignatureFlowService.Type.GUARANTORUSER.value: 0,
            SignatureFlowService.Type.INPUT.value: 0,
            SignatureFlowService.Type.OUTPUT.value: 0
        }

        if signature_flow_id:
            sf = SignatureFlow(pk=int(signature_flow_id))
        else:
            sf = SignatureFlow(name='', description='')

        for key, n in graph['nodes'].items():
            properties = {'position': n['position']}
            user = None
            if n['name'] in [SignatureFlowService.Type.SIGNINGUSER.value,  
                            SignatureFlowService.Type.GUARANTORUSER.value]:
                if n['data'] and n['data']['user_id'] and n['data']['user_id'] != '-1':
                    user = User(int(n['data']['user_id']))
                else:
                    raise ValidationError("Debe seleccionar un usuario para cada estado")

            if n['name'] != SignatureFlowService.Type.INPUT.value:
                if not n['inputs']['in']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")

            if n['name'] != SignatureFlowService.Type.OUTPUT.value:  
                if not n['outputs']['out']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")
                
            acc[n['name']] += 1
            node = SignatureNode(
                type=n['name'], 
                index=n['id'],
                user=user,
                properties=json.dumps(properties),
                signature_flow=sf)
            node_list.append(node)

        if acc[SignatureFlowService.Type.INPUT.value] > 1 or acc[SignatureFlowService.Type.OUTPUT.value] > 1:
            raise ValidationError("Solo se permiten un nodo de entrada y un nodo de salida")
        if acc[SignatureFlowService.Type.INPUT.value] == 0 or acc[SignatureFlowService.Type.OUTPUT.value] == 0:
            raise ValidationError("Se requiere un nodo de entrada y un nodo de salida")

        if signature_flow_id:
            SignatureNode.objects.filter(signature_flow__id=signature_flow_id).delete()
        else:
            sf.save()
        node_list = SignatureNode.objects.bulk_create(node_list)

        for n in node_list:
            nodes[n.index] = n
        
        for key, n in nodes.items():
            if graph['nodes'][str(key)]['inputs']:
                previous = [nodes[c['node']] for c in graph['nodes'][str(key)]['inputs']['in']['connections']]
                n.previous.set(previous)
        return sf

    @classmethod
    def get_initial_json(cls):
        graph = {
            "id": "demo@0.1.0",
            "nodes": {
                "1": {
                "id": 1,
                "data": {},
                "inputs": {},
                "outputs": {
                    "out": {
                    "connections": []
                    }
                },
                "position": [
                    0,
                    100
                ],
                "name": "Inicio"
                },
                "2": {
                "id": 2,
                "data": {},
                "inputs": {
                    "in": {
                    "connections": []
                    }
                },
                "outputs": {},
                "position": [
                    800,
                    100
                ],
                "name": "Fin"
                },
            }
        }
        return graph
        

