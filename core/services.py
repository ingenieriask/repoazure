from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging

from core.models import AppParameter

logger = logging.getLogger(__name__)

class MailService(object):
    '''Basic email sender'''

    _params = {}

    @classmethod
    def send_mail(cls, subject='', body='', from_email=None, to=None):
        '''Send emails to several addresses using database parameters'''
        
        # Lazy load
        if not cls._params:
            # Get only email related parameters
            qs = AppParameter.objects.filter(name__startswith='EMAIL_')
            cls._params = {entry.name : entry.value for entry in qs}

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

