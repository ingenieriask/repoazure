from django.shortcuts import render

def cubes(request):
    return render(request, 'reports/dashboard.html')