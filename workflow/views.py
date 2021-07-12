from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib import messages
import json
from workflow.services import SignatureFlowService
from workflow.forms import SignatureFlowForm

def signature(request, radicate):

    graph_error = ''
    if request.method == 'POST':
        form = SignatureFlowForm(request.POST)
        if form.is_valid():
            print('valid')
            #return HttpResponseRedirect(reverse('')
        graph = json.loads(request.POST['graph'])
        
        try:
            sf = SignatureFlowService.from_json(json.loads(request.POST['graph']))
            print('sf:', sf)
        except ValidationError as e:
            messages.error(request, e.message)
        except:
            messages.error(request, "Something else went wrong")

    if request.method == 'GET':
        form = SignatureFlowForm(request.GET)
        graph = SignatureFlowService.to_json(1)
        print('graph:', graph)

    return render(
        request,
        'workflow/signature_flow.html',
        context={
            'form': form,
            'widget': {
                'graph': graph,
            },
            'radicate': radicate,
            'grapherror' : graph_error
        })
