from django import template
from PIL import ImageColor

register = template.Library()

@register.filter()
def change_size_unit(value, unit):
    return str(value)+unit

@register.filter()
def dark(value):
    r, g, b = ImageColor.getcolor(value, "RGB")
    r *= 0.8
    g *= 0.8
    b *= 0.8
    return str('rgba('+ str(int(r)), str(int(g)), str(int(b))+')')