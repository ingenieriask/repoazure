from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.

def holidays(request):

    # request should be ajax and method should be POST.
    if request.is_ajax and request.method == "POST":