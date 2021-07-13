from django.conf.urls import url
from pqrs import views
from django.urls import path

app_name = 'pqrs'

urlpatterns = [
    path('', views.index, name='index'),
    path('pqrs-create/<uuid:pqrs>/', views.create_pqr_multiple, name='pqrs_create_multiple_person'),
    path('pqrs-detail/<int:pk>/', views.PqrDetailView.as_view(), name="pqrs_detail"),
    path('pqrs-finish-creation/<int:pk>/', views.PqrFinishCreation.as_view(), name="pqrs_finish_creation"),
    path('pqrs-type/<int:applicanType>/', views.PQRSType, name='pqrs_type'),
    path('search-person/<int:pqrs_type>/<int:person_type>/', views.search_person, name='search_person'),
    path('person-type/<int:pqrs_type>/<int:applicanType>/', views.person_type, name='person_type'),
    path('send-email-person/<int:pk>/<int:pqrs_type>/', views.send_email_person, name='send_email_person'),
    path('validate-email-person/<str:uuid_redis>/', views.validate_email_person, name='validate_email_person'),
    path('select/', views.select, name='select'),
    path('create-person/<str:pqrs_type>/', views.PersonCreateView.as_view(), name='create_person'),
    path('create-legal-person/<str:pqrs_type>/', views.LegalPersonCreateView.as_view(), name='create_legal_person'),
    path('create-person-attorny/<uuid:pqrs_type>/', views.PersonAtronyCreate.as_view(), name='create_person_attorny'),
    path('create-person-request/<uuid:pqrs_type>/', views.PersonRequestCreateView.as_view(), name='create_person_request'),
    path('edit-person/<uuid:pqrs_type>/<int:pk>/', views.PersonUpdateViewNew.as_view(), name='edit_person'),
    path('edit-person-request/<uuid:pqrs_type>/<int:pk>/', views.PersonUpdateViewNewRequest.as_view(), name='edit_person_request'),
    path('multi-request/<uuid:person>/', views.multi_create_request, name='multi_request'),
    path('delete-person/<uuid:pqrs_type>/<int:id>/',views.dete_person_request, name='delete_person_request'),
    path('radicate/inbox/', views.RadicateInbox.as_view(), name='radicate_inbox'),
    path('radicate/my-inbox/', views.RadicateMyInbox.as_view(), name='radicate_my_inbox'),
    path('radicate/my-reported/', views.RadicateMyReported.as_view(), name='radicate_my_reported'),
    path('radicate/<int:pk>/', views.PqrDetailProcessView.as_view(), name="detail_pqr"),
    path('conclusion/', views.procedure_conclusion, name='conclusion'),
    path('consultant/', views.pqrsConsultan, name="pqrs_consultant"),
    path('consultation/result/<int:pk>/', views.PqrsConsultationResult.as_view(), name="consultation_result"),
    path('extend-request/<int:pk>', views.pqrs_extend_request, name='extend_request'),
    path('answer-request/<int:pk>', views.pqrs_answer_request, name="answer_request"),
    path('answer/<int:pk>', views.pqrs_answer, name='answer'),
    path('validate-captcha/<uuid:pqrs>/', views.validate_captcha, name='validate-captcha')
]
