from django import template
from django.contrib.auth.models import Permission
from core.models import Menu, FunctionalArea
from django.urls import reverse

register = template.Library()

@register.filter(is_safe=True)
def format_percent(value: float, args: str = ""):
    """
    Format a numeric value as percentage
    :param value: the numeric value
    :param args: a CSV string of arguments to the formatting operation
    :return: the formatted value
    """
    include_symbol = False
    # splits the arguments string into a list of arguments
    arg_list = [arg.strip() for arg in args.split(',')] if args else []
    # sets the precision (number of decimal digits)
    precision = int(arg_list[0]) if len(arg_list) > 0 else 0
    # should the "%" symbol be included?
    include_symbol = bool(arg_list[1]) if len(arg_list) > 1 else False
    symbol = "%" if include_symbol else ""
    # builds and returns the formatted value
    return f"{value * 100.0:.{precision}f}{symbol}"

def _get_user_permissions(user):
    if user.is_superuser:
        return Permission.objects.all()
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def has_children(menu):
    return 'children' in menu and bool(menu['children'])

@register.filter
def has_permission(link):
    return 'enabled' in link and link['enabled'] 

@register.filter
def get_link(menu):
    """Safe url replacement method"""

    url_name = menu['data']['url_name']
    try:
        url_name = menu['data']['url_name']
        return reverse(url_name)
    except:
        print(f"{url_name} is not a registered namespace")
    return "unregistered-namespace"

def check_links(link, permissions):

    is_empty = not bool(link['data']['required_permissions'])
    link['enabled'] = is_empty or bool(permissions & set(link['data']['required_permissions']))

    if 'children' in link and bool(link['children']):
        enabled_child = False
        for child in link['children']:
            enabled_child = check_links(child, permissions) or enabled_child
        link['enabled'] = link['enabled'] and enabled_child

    return link['enabled']


@register.inclusion_tag('correspondence/menu.html', takes_context=True)
def menu(context):
    """Generate the main menu based on user permissions"""

    user = context['request'].user
    permissions = _get_user_permissions(user)
    permissions = {p.id for p in permissions if not p.codename.startswith(('add_', 'change_', 'delete_', 'view_'))}
    root = Menu.objects.filter(name='main_menu').first()
    link = Menu.dump_bulk(root)

    check_links(link[0], permissions)

    return {'links': link[0]['children'], 'user': context['user'], 'perms': context['perms']}
