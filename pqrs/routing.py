from django.urls import path
from .consumers import WSconsumer

ws_urlpatterns=[
    path('ws/some_url/<uuid:code_room>/',WSconsumer.as_asgi())
]