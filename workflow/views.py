from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponseRedirect
import json
from workflow.services import FlowService

def signature(request, radicate):

    graph_error = ''
    if request.method == 'POST':
        id = request.POST['id']
        next_view = request.POST['next']
        graph = json.loads(request.POST['graph'])
        try:
            sf = FlowService.from_json(graph, FlowService.FlowType.SIGNATURE, id if id and id != 'None' else None)
            id = sf.id
        except ValidationError as e:
            messages.error(request, e.message)
        except:
            messages.error(request, "Something else went wrong")
        if next_view and next_view != 'None':
            return HttpResponseRedirect(reverse(next_view))

    if request.method == 'GET':
        next_view = request.GET.get('next')
        id = request.GET.get('id')
        graph = FlowService.to_json(id, FlowService.FlowType.SIGNATURE)

    return render(
        request,
        'workflow/signature_flow.html',
        context={
            'id': id,
            'graph': graph,
            'radicate': radicate,
            'grapherror' : graph_error,
            'next': next_view
        })

def filing(request, radicate):

    graph_error = ''
    if request.method == 'POST':
        id = request.POST['id']
        next_view = request.POST['next']
        graph = json.loads(request.POST['graph'])
        try:
            sf = FlowService.from_json(graph, None, id if id and id != 'None' else None)
            id = sf.id
        except ValidationError as e:
            messages.error(request, e.message)
        except:
            messages.error(request, "Something else went wrong")
        if next_view and next_view != 'None':
            return HttpResponseRedirect(reverse(next_view))
            
    if request.method == 'GET':
        next_view = request.GET.get('next')
        id = request.GET.get('id')
        graph = FlowService.to_json(id)

    return render(
        request,
        'workflow/filing_flow.html',
        context={
            'id': id,
            'graph': graph,
            'radicate': radicate,
            'grapherror' : graph_error,
            'next': next_view
        })
