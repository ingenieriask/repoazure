from django import template

register = template.Library()

@register.filter()
def change_size_unit(value, unit):
    return str(value)+unit
