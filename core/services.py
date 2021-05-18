from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage

from core.models import AppParameter

class MailService(object):
    '''Basic email sender'''

    @classmethod
    def send_mail(self, subject='', body='', from_email=None, to=None):
        '''Send emails to several addresses using database parameters'''
        
        # Get only email related parameters
        qs = AppParameter.objects.filter(name__startswith='EMAIL_')
        params = {entry.name : entry.value for entry in qs}

        if not from_email:
            from_email = params['EMAIL_HOST_USER']

        print('params:', params)

        # Configure email handler
        eb = EmailBackend(
            host=params['EMAIL_HOST'], 
            port=int(params['EMAIL_PORT']), 
            username=params['EMAIL_HOST_USER'], 
            password=params['EMAIL_HOST_PASSWORD'], 
            use_tls=bool(params['EMAIL_USE_TLS']), 
            fail_silently=False)
        eb.open()

        email = EmailMessage(subject, body, from_email, to)

        # Send email
        eb.send_messages([email])
        eb.close()
