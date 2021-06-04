
from core.models import SystemParameter
from django.core.mail import EmailMultiAlternatives
from core.utils import replace_data
import logging
import re
import json

logger = logging.getLogger(__name__)

def get_system_parameter(format_name):
    print('format_name:', format_name)
    return SystemParameter.objects.get(name=format_name)

def get_json_system_parameter(format_name):
    return json.loads(get_system_parameter(format_name).value)

def process_email(format_name, recipient_list, data):
    try:
        email_format = get_system_parameter(format_name)
        email_format = json.loads(email_format.value)

        msg = EmailMultiAlternatives(
            replace_data(email_format['subject'], data),
            replace_data(email_format['body'], data),
            'rino@skillnet.com.co',
            [recipient_list],
        )
        msg.content_subtype = "html"
        msg.send()
    except Exception as Error:
        print('error de envío de correo', Error)
        logger.error(Error)
        # messages.error(self.request,"Ha ocurrido un error al actualizar el expediente en el gestor de contenido")
