from django.conf.urls import url
from pqrs import views
from django.urls import path

app_name = 'pqrs'

urlpatterns = [
    path('', views.index, name='index'),
    path('pqrs-create/<int:person>/', views.create_pqr, name='pqrs_create'),
    path('pqrs-create/<uuid:pqrs>/', views.create_pqr, name='pqrs_create'),
    path('pqrs-detail/<int:pk>/', views.PqrDetailView.as_view(), name="pqrs_detail"),
    path('pqrs-type/', views.PQRSType, name='pqrs_type'),
    path('search-person/<int:pqrs_type>/', views.search_person, name='search_person'),
    path('send-email-person/<int:pk>/', views.send_email_person, name='send_email_person'),
    path('validate-email-person/<str:uuid>/', views.validate_email_person, name='validate_email_person'),
    path('select/', views.select, name='select'),
    #path('edit-person/<int:pk>/<str:uuid>/', views.PersonUpdateView.as_view(), name='edit_person'),
    path('create-person/', views.PersonCreateView.as_view(), name='create_person'),
    path('create-person-request/<str:arguments>/', views.PersonRequestCreateView.as_view(), name='create_person_request'),
    path('edit-person/<str:arguments>/<int:pk>/', views.PersonUpdateViewNew.as_view(), name='edit_person'),
    path('edit-person-request/<str:arguments>/<int:pk>/', views.PersonUpdateViewNewRequest.as_view(), name='edit_person_request'),
    path('multi-request/<str:person>/', views.multi_create_request, name='multi_request'),
    path('delete-person/<str:arguments>/<int:id>/',views.dete_person_request, name='delete_person_request'),
    
]