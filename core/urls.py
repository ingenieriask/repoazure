from django.conf.urls import url
from core import views
from django.urls import path

app_name = 'core'

urlpatterns = [
    path('holidays', views.index, name='holidays'),
    path('weekends', views.index, name='weekends'), 
]
path('pqrs-create/<int:person>/', views.create_pqr, name='pqrs_create'),