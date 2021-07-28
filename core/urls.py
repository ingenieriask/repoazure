from django.conf.urls import url
from core import views
from core.services import Scheduler
from django.urls import path


app_name = 'core'

urlpatterns = [
    path('home_global.css/', views.StyleSettingsView.as_view(), name='home-global'),
    path('test-quill/<int:pk>/', views.TestViewQuill.as_view(), name='test_view'),
    path('test-tiny/<int:pk>/', views.TestViewTiny.as_view(), name='test_view'),
]