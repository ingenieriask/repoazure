from django import template
from core.services import CalendarService

register = template.Library()

@register.filter(expects_localtime=True)
def getMissingDays(request_day, max_response_days):
    missingDays = CalendarService.get_remaining_business_days(request_day, max_response_days)
    return missingDays


@register.filter(expects_localtime=True)
def getColorTrafficLight(alerts, request_day):
    alerts = alerts.order_by('response_time')
    days_since_radicate = CalendarService.get_business_days_since(request_day)
    color = "#009900"
    for alert in alerts:
        if days_since_radicate >= alert.response_time:
            color = alert.color
    return color