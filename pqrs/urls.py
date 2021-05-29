from django.conf.urls import url
from pqrs import views
from django.urls import path

app_name = 'pqrs'

urlpatterns = [
    path('', views.index, name='index'),
    path('pqrs-create/<int:person>/', views.create_pqr, name='pqrs_create'),
    path('pqrs-detail/<int:pk>/', views.PqrDetailView.as_view(), name="pqrs_detail"),
    path('pqrs-type/', views.PersonCreateView.as_view(), name='create_person'),
    path('search-person/', views.search_person, name='search_person'),
    path('send-email-person/<int:pk>/', views.send_email_person, name='send_email_person'),
    path('validate-email-person/<str:uuid>/', views.validate_email_person, name='validate_email_person'),
    path('select/', views.select, name='select'),
    path('edit-person/<int:pk>/<str:uuid>/', views.PersonUpdateView.as_view(), name='edit_person'),
    path('create-person/', views.PersonCreateView.as_view(), name='create_person')
]