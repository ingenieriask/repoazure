
from core.models import SystemParameter
from django.core.mail import EmailMultiAlternatives
import logging
import re
import json


logger = logging.getLogger(__name__)


def get_system_parameter(format_name):
    print('format_name:', format_name)
    return SystemParameter.objects.get(name=format_name)


def get_json_system_parameter(format_name):
    return json.loads(get_system_parameter(format_name).value)
