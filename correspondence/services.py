from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import logging

from core.models import AppParameter

logger = logging.getLogger(__name__)

class ECMService(object):
    '''ECM handler for Alfresco'''

    _params = {}

    @classmethod
    def upload(cls, files=None, data=None):
        '''TODO'''
        
        # Lazy load
        if not cls._params:
            # Get only email related parameters
            qs = AppParameter.objects.filter(name__startswith='ECM_')
            cls._params = {entry.name : entry.value for entry in qs}

        print(cls._params)


