from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging
from datetime import datetime
from django.db import transaction
import  re

from core.models import AppParameter, ConsecutiveFormat, Consecutive, FilingType

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