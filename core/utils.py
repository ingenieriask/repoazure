# from django.contrib import messages
import logging
import re

logger = logging.getLogger(__name__)


def get_field_value(obj, field_name):
    try:
        return obj[field_name]
    except Exception as Error:
        return None

def anonymize(text):
    ret = ''
    for t in re.findall(r"[\w']+|[@]", text):
        t = t.strip()
        if len(t) > 2:
            ret += t[0] + '*' * (len(t) - 2) + t[len(t)-1] + ' '
        else:
            ret += t + ' '
    return ret.strip()