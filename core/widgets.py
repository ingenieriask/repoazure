from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from django.http import JsonResponse
import json
from datetime import date
from core.services import RecordCodeService
from core.models import CalendarDay

class ConsecutiveFormatWidget(forms.Widget):
    '''Custom widget for the consecutive format definition'''

    template_name = 'core/consecutive_format_widget.html'

    def get_context(self, name, value, attrs=None):

        format, digits = RecordCodeService.decompile(value)
        return {'widget': {
            'name': name,
            'value': format,
            'digits': digits,
            'options': RecordCodeService.tokens,
            'colors': ['bg-primary', 'bg-success', 'bg-warning']
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class NonWorkingCalendarWidget(forms.Widget):
    '''Custom widget for non-working days configuration'''

    template_name = 'core/year_calendar_widget.html'

    def get_context(self, name, value, attrs=None):
        year = date.today().year
        return {'widget': {
            'name': name,
            'value': value,
            'year': year,
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

class SignatureFlowWidget(forms.Widget):
    ''' '''

    template_name = 'core/signature_flow.html'

    def get_context(self, name, value, attrs=None):

        value = 1 # TDOO: just for test
        if value:
            graph = self.get_json(value)
        else:
            graph = self.get_initial_json()

        return {'widget': {
            'name': name,
            'graph': graph
        }}

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

    def get_initial_json(self):
        graph = {
            "id": "demo@0.1.0",
            "nodes": {
                "1": {
                "id": 1,
                "data": {},
                "inputs": {},
                "outputs": {
                    "out": {
                    "connections": []
                    }
                },
                "position": [
                    0,
                    100
                ],
                "name": "Inicio"
                },
                "2": {
                "id": 2,
                "data": {},
                "inputs": {
                    "in": {
                    "connections": []
                    }
                },
                "outputs": {},
                "position": [
                    800,
                    100
                ],
                "name": "Fin"
                },
            }
        }
        return graph

    def get_json(self, value):
        graph = {
            "id": "demo@0.1.0",
            "nodes": {
                "1": {
                "id": 1,
                "data": {},
                "inputs": {},
                "outputs": {
                    "out": {
                    "connections": [
                        {
                        "node": 4,
                        "input": "in",
                        "data": {}
                        }
                    ]
                    }
                },
                "position": [
                    0,
                    100
                ],
                "name": "Inicio"
                },
                "2": {
                "id": 2,
                "data": {},
                "inputs": {
                    "in": {
                    "connections": [
                        {
                        "node": 6,
                        "output": "out",
                        "data": {}
                        },
                        {
                        "node": 5,
                        "output": "out",
                        "data": {}
                        }
                    ]
                    }
                },
                "outputs": {},
                "position": [
                    800,
                    100
                ],
                "name": "Fin"
                },
                "4": {
                "id": 4,
                "data": {
                    "user_id": 4
                },
                "inputs": {
                    "in": {
                    "connections": [
                        {
                        "node": 1,
                        "output": "out",
                        "data": {}
                        }
                    ]
                    }
                },
                "outputs": {
                    "out": {
                    "connections": [
                        {
                        "node": 5,
                        "input": "in",
                        "data": {}
                        },
                        {
                        "node": 6,
                        "input": "in",
                        "data": {}
                        }
                    ]
                    }
                },
                "position": [
                    282,
                    173
                ],
                "name": "Avalador"
                },
                "5": {
                "id": 5,
                "data": {
                    "user_id": "8"
                },
                "inputs": {
                    "in": {
                    "connections": [
                        {
                        "node": 4,
                        "output": "out",
                        "data": {}
                        }
                    ]
                    }
                },
                "outputs": {
                    "out": {
                    "connections": [
                        {
                        "node": 2,
                        "input": "in",
                        "data": {}
                        }
                    ]
                    }
                },
                "position": [
                    530,
                    19.199996948242188
                ],
                "name": "Firmante"
                },
                "6": {
                "id": 6,
                "data": {
                    "user_id": "16"
                },
                "inputs": {
                    "in": {
                    "connections": [
                        {
                        "node": 4,
                        "output": "out",
                        "data": {}
                        }
                    ]
                    }
                },
                "outputs": {
                    "out": {
                    "connections": [
                        {
                        "node": 2,
                        "input": "in",
                        "data": {}
                        }
                    ]
                    }
                },
                "position": [
                    527,
                    214.1999969482422
                ],
                "name": "Firmante"
                }
            }
        }
        return graph







