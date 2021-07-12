from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponseRedirect
import json
from workflow.services import SignatureFlowService
from workflow.forms import SignatureFlowForm

def signature(request, radicate):

    graph_error = ''
    if request.method == 'POST':
        form = SignatureFlowForm(request.POST)
        id = request.POST['id']
        next_view = request.POST['next']
        graph = json.loads(request.POST['graph'])
        sf = SignatureFlowService.from_json(graph, id if id and id != 'None' else None)
        id = sf.id
        try:
            sf = SignatureFlowService.from_json(graph, id if id else None)
        except ValidationError as e:
            messages.error(request, e.message)
        except:
            messages.error(request, "Something else went wrong")
        if next_view and next_view != 'None':
            return HttpResponseRedirect(reverse(next_view))

    if request.method == 'GET':
        next_view = request.GET.get('next')
        id = request.GET.get('id')
        graph = SignatureFlowService.to_json(id)

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
