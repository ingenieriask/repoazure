from django.shortcuts import render, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.http import urlencode

from .models import Poll, PollInstance

# Create your views here.

def show_poll(request, pk):
    
    try:
        poll = Poll.objects.get(type_poll=pk)
    except:
        messages.error(request, "Poll does not exists!")
        return render(request, 'polls/show_poll.html')

    if request.method=='POST':
        
        answers_list = []
        answers = list(request.POST.items())[1:]
        answers.sort()
        for answer in answers:
            answers_list.append(answer[1])
            
        PollInstance(poll = poll, answers = answers_list).save()
        get_args_str = urlencode({'template': 'PROCEDURE_CONCLUSION', 'destination': 'index'})
        return HttpResponseRedirect(reverse('pqrs:conclusion')+'?'+get_args_str)
        
    poll_questions = poll.questions.order_by('number')
    
    return render(request, 'polls/show_poll.html', {'poll_questions': poll_questions})