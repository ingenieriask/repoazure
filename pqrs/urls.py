from django.conf.urls import url
from pqrs import views
from django.urls import path

app_name = 'pqrs'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    path('pqrs_create/<int:person>/', views.create_pqr, name='pqrs_create'),
    path('pqrs_detail/<int:pk>/', views.PqrDetailView.as_view(), name="pqrs_detail"),
    path('search_person/', views.search_person, name='search_person'),
    path('send_email_person/<int:pk>/', views.send_email_person, name='send_email_person'),
    path('validate_email_person/<str:uuid>/', views.validate_email_person, name='validate_email_person'),
    path('select/', views.select, name='select'),
    path('edit_person/<int:pk>/<str:uuid>/', views.PersonUpdateView.as_view(), name='edit_person'),
    path('create_person/', views.PersonCreateView.as_view(), name='create_person')
]