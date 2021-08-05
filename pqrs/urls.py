from django.conf.urls import url
from pqrs import views, views_persons, views_statistics
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
    path('create-person/<str:pqrs_type>/', views_persons.PersonCreateView.as_view(), name='create_person'),
    path('create-legal-person/<str:pqrs_type>/', views_persons.LegalPersonCreateView.as_view(), name='create_legal_person'),
    path('create-person-attorny/<uuid:pqrs_type>/', views_persons.PersonAtronyCreate.as_view(), name='create_person_attorny'),
    path('create-person-request/<uuid:pqrs_type>/', views_persons.PersonRequestCreateView.as_view(), name='create_person_request'),
    path('edit-person/<uuid:pqrs_type>/<int:pk>/', views_persons.PersonUpdateViewNew.as_view(), name='edit_person'),
    path('edit-person-request/<uuid:pqrs_type>/<int:pk>/', views_persons.PersonUpdateViewNewRequest.as_view(), name='edit_person_request'),
    path('multi-request/<uuid:person>/', views.multi_create_request, name='multi_request'),
    path('delete-person/<uuid:pqrs_type>/<int:id>/',views.dete_person_request, name='delete_person_request'),
    path('radicate/inbox/', views.RadicateInbox.as_view(), name='radicate_inbox'),
    path('radicate/my-inbox/', views.RadicateMyInbox.as_view(), name='radicate_my_inbox'),
    path('radicate/my-reported/', views.RadicateMyReported.as_view(), name='radicate_my_reported'),
    path('radicate/email-inbox/', views.RadicateEmailInbox.as_view(), name='radicate_email_inbox'),
    path('radicate/<int:pk>/', views.PqrDetailProcessView.as_view(), name="detail_pqr"),
    path('radicate-assign/<int:pk>/', views.PqrDetailAssignView.as_view(), name="asign_detail_pqr"),
    path('radicate-email/<int:pk>/', views.PqrDetailEmailView.as_view(), name="email_detail_pqr"),
    path('radicate-reported/<int:pk>/', views.PqrDetailReportedView.as_view(), name="reported_detail_pqr"),
    path('radicate-detail/<int:pk>/', views.AssociatedRadicateDetailView.as_view(), name='associated_radicate_detail'),
    path('conclusion/', views.procedure_conclusion, name='conclusion'),
    path('consultant/', views.pqrsConsultan, name="pqrs_consultant"),
    path('consultation/result/<int:pk>/', views.PqrsConsultationResult.as_view(), name="consultation_result"),
    path('extend-request/<int:pk>', views.pqrs_extend_request, name="extend_request"),
    path('radicate-associate/<int:pk>/', views.pqrs_associate_request, name="associate_detail_pqr"),
    path('answer-request/<int:pk>', views.pqrs_answer_request, name="answer_request"),
    path('answer-request-email/<str:uuid_redis>', views.pqrs_answer_request_email, name="answer_request_email"),
    path('answer/<int:pk>/<int:actualPk>', views.pqrs_answer, name='answer'),
    path('answer-preview/<int:pk>', views.pqrs_answer_preview, name='answer_preview'),
    path('validate-captcha/<uuid:pqrs>/', views.validate_captcha, name='validate-captcha'),
    path('consultation/zip/<int:pk>', views.get_consultation_zip, name="consultation_zip"),
    path('change-classification/<int:pk>', views.change_classification, name="change_clasification"),
    path('bring-subtype/', views.bring_subtype, name="bring_subtype"),
    path('pqrs-consultant/', views.search_pqrsd, name='consultant_view'),
    path('statistics/', views_statistics.PqrsStatistics.as_view(), name='statistics'),
    path('horizontal-bar-chart/', views_statistics.calculate_horizontal_bar_chart, name="horizontal-bar-chart"),
    path('person-type-chart/', views_statistics.calculate_person_type_chart, name='person-type-chart'),
    path('state-chart/', views_statistics.calculate_state_chart, name='state-chart'),
    path('channel-chart/', views_statistics.calculate_channel_chart, name='channel-chart'),
    path('ethnic-group-chart/', views_statistics.calculate_ethnic_group_chart, name="ethnic-group-chart"),
    path('disability-condition-chart/', views_statistics.calculate_disability_condition_chart, name='disability-condition-chart'),
    path('conflict-victim-chart/', views_statistics.calculate_conflict_victim_chart, name='conflict-victim-chart'),
    path('preferential-population-chart/', views_statistics.calculate_preferential_population_chart, name='preferential-population-chart'),
    path('gender-chart', views_statistics.calculate_gender_chart, name='gender-chart'),
    path('ontime-chart', views_statistics.calculate_ontime_chart, name='ontime-chart'),
    path('calculate-statistics/', views_statistics.calculate_statistics, name='calculate-statistics'),
    path('records-form/', views.records_form, name='records_form'),
    path('records-form-param/<int:pk>/', views.records_form_param, name='records_form_parameter'),
    path('records-detail/<int:pk>/', views.RecordDetailView.as_view(), name='records_detail'),
    path('records-list/', views.RecordListView.as_view(), name='records_list'),
    path('create-room/', views.create_room, name='create_room'),
]
