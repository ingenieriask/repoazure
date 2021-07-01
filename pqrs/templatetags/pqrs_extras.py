import re
from django import template
from core.services import CalendarService
import datetime

register = template.Library()

@register.filter(expects_localtime=True)
def get_missing_days(request_day, max_response_days):
    missingDays = CalendarService.get_remaining_business_days(request_day, max_response_days)
    return missingDays


@register.filter(expects_localtime=True)
def get_color_traffic_light(alerts, request_day):
    alerts = alerts.order_by('response_time')
    days_since_radicate = CalendarService.get_business_days_since(request_day)
    color = "#009900"
    for alert in alerts:
        if days_since_radicate >= alert.response_time:
            color = alert.color
    return color


@register.filter(expects_localtime=True)
def simple_date(date):   
    return date.strftime('%d/%m/%Y')
    

@register.filter(expects_localtime=True)
def max_response_date(date_radicated, max_response_days):
    response_date = date_radicated + datetime.timedelta(days=max_response_days)
    return response_date.strftime('%d/%m/%Y')

@register.filter()
def size_metric(size, metric):
    if metric == "MB":
        size /= 1000
        
    return "{:.1f}".format(size)