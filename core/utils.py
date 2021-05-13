# from django.contrib import messages
import logging
import re

logger = logging.getLogger(__name__)


def get_field_value(obj, field_name):
    try:
        return obj[field_name]
    except Exception as Error:
        return None


def get_data_from_obj(param, obj):
    arr = param.split(".", 1)
    if len(arr) == 1:
        try:
            return obj.__dict__[arr[0]]
        except Exception as Error:
            try:
                return obj[arr[0]]
            except Exception as Error:
                try:
                    return eval('obj.' + arr[0])
                except Exception as Error:
                    return ''
    try:
        return get_data_from_obj(arr[1], eval('obj.' + arr[0]))
    except Exception as Error:
        return ''


def replace_data(text, obj):
    for par in re.compile('<param>(.*?)</param>', re.IGNORECASE).findall(text):
        text = text.replace('<param>' + par + '</param>', get_data_from_obj(par, obj))
    return text

def anonymize(text):
    ret = ''
    for t in re.findall(r"[\w']+|[@]", text):
        t = t.strip()
        if len(t) > 2:
            ret += t[0] + '*' * (len(t) - 2) + t[len(t)-1] + ' '
        else:
            ret += t + ' '
    return ret.strip()