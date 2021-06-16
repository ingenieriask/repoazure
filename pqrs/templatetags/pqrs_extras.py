from django import template
from datetime import datetime, timedelta, date

register = template.Library()

@register.filter(expects_localtime=True)
def sumDates(iniDate, maxDays):
    days = ((iniDate + timedelta(maxDays)) - datetime.now())
    return days.days