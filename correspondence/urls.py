from django.conf.urls import url
from correspondence import views
from django.urls import path

import correspondence.api_views

app_name = 'correspondence'

urlpatterns = [
    path('api/v1/radicates/', correspondence.api_views.RadicateList.as_view(), name='search_radicates'),
    url(r'^$', views.index, name='index'),
    path('search-names/', views.search_names, name='search_names'),
    path('users-by-area/', views.users_by_area, name='users_by_area'),
    path('return-to-last-user/<int:radicate>', views.return_to_last_user, name='return_to_last_user'),
    path('report-to-user/<int:radicate>', views.report_to_user_area, name='report_to_user'),
    path('assign-user/<int:radicate>', views.assign_user, name='assign_user'),
    # path('assign-user/<int:radicate>/<int:area>', views.assign_user_area, name='assign_user'),
    path('search-content/', views.search_by_content, name='search_by_content'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('radicate/create/<int:person>/', views.create_radicate, name='create_radicate'),
    path('radicate/list/', views.RadicateList.as_view(), name='list_radicate'),
    path('radicate/<int:pk>/', views.RadicateDetailView.as_view(), name="detail_radicate"),
    path('radicate-detail/<str:cmis_id>/', views.detail_radicate_cmis, name="detail_radicate_cmis"),
    path('edit-radicate/<int:id>/', views.edit_radicate, name='edit_radicate'),
    path('current-user/<int:pk>/', views.CurrentUserUpdate.as_view(), name='current_user'),
    path('recordassigned/<int:pk>/', views.RecordAssignedUpdate.as_view(), name='recordassigned'),
    path('person/create/', views.PersonCreateView.as_view(), name='create_person'),
    path('person/<int:pk>/', views.PersonDetailView.as_view(), name='detail_person'),
    path('edit-person/<int:pk>/', views.PersonUpdateView.as_view(), name='edit_person'),
    path('register/', views.register, name='register'),
    path('charts/', views.charts, name='charts'),
    path('project-answer/<int:pk>/', views.project_answer, name='project_answer'),
    path('record/create/', views.RecordCreateView.as_view(), name='create_record'),
    path('record-detail/<int:pk>/', views.RecordDetailView.as_view(), name='detail_record'),
    path('record/edit/<int:pk>/', views.RecordUpdateView.as_view(), name='edit_record'),
    path('record/list/', views.RecordListView.as_view(), name='list_records'),
    path('record/process-excel-radicates/', views.ProcessExcelRadicates.as_view(), name='process_excel_radicates'),
    path('radicate/thumbnail/', views.get_thumbnail, name='get_thumbnail'),
    path('template/list/', views.TemplateListView.as_view(), name='template_list'),
    path('template/create', views.TemplateCreateView.as_view(), name='create_template'),
    path('template/edit/<int:pk>/', views.TemplateEditView.as_view(), name='edit_template')
]
