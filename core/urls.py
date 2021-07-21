from django.conf.urls import url
from core import views
from django.urls import path


app_name = 'core'

urlpatterns = [
    path('home_global.css/', views.StyleSettingsView.as_view(), name='home-global')
]