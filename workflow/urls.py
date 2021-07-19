from django.conf.urls import url
from django.urls import path
from workflow import views

app_name = 'workflow'

urlpatterns = [
    path('signature/<int:radicate>', views.signature, name='signature'),
    path('filing/<int:radicate>', views.filing, name='filing')
]
