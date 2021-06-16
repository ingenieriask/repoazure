from django.conf.urls import url
from polls import views
from django.urls import path

app_name = 'polls'

urlpatterns = [
    path('show_poll/<int:pk>/', views.show_poll, name="show_poll"),
]