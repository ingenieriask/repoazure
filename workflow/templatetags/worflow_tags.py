from django import template
from django.contrib.auth.models import Permission
from core.models import FunctionalArea
from django.urls import reverse

register = template.Library()

@register.inclusion_tag('workflow/find_user.html', takes_context=True)
def find_user(context, target=None):

    functional_tree = []
    for item, info in FunctionalArea.get_annotated_list():
            temp = False
            if info['level'] != 0 and int(item.parent.get_depth() + info['level']) > item.get_depth():
                temp = True
            functional_tree.append((item, info, temp))

    result = {'functional_tree': functional_tree}
    if target:
        result['target'] = target
    return result
