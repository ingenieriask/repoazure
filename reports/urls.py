# -*- coding: utf-8 -*-
try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls import url

from .api import (
    ApiVersion, Index, Info, ListCubes,
    CubeModel, CubeAggregation, CubeCell,
    CubeReport, CubeFacts, CubeFact, CubeMembers
)

from django.urls import path
from reports import views

app_name = 'reports'

urlpatterns = [
    url(r'^$', Index.as_view(), name='index'),
    path('version/', ApiVersion.as_view(), name="version"),
    path('info/', Info.as_view(), name="info"),
    path('cubes/', ListCubes.as_view(), name="cubes"),
    path('cube/<str:cube_name>/model/', CubeModel.as_view(), name="cube_model"),
    path('cube/<str:cube_name>/aggregate/', CubeAggregation.as_view(), name="cube_aggregation"),
    path('cube/<str:cube_name>/cell/', CubeCell.as_view(), name="cube_cell"),
    path('cube/<str:cube_name>/report/', CubeReport.as_view(), name="cube_report"),
    path('cube/<str:cube_name>/facts/', CubeFacts.as_view(), name="cube_facts"),
    path('cube/<str:cube_name>/fact/<str:fact_id>/', CubeFact.as_view(), name="cube_fact"),
    path('cube/<str:cube_name>/members/<str:dimension_name>/', CubeMembers.as_view(), name="cube_members"),
    path('dashboard/', views.cubes, name="dashboard"),
    #url(r'cube/(?P<cube_name>\S+)/facts/$', CubeFacts.as_view(), name='cube_facts'),
]


'''
url(r'^reports$', Index.as_view(), name='index'),
url(r'^reports/version/$', ApiVersion.as_view(), name='version'),
url(r'^reports/info/$', Info.as_view(), name='info'),
url(r'^reports/cubes/$', ListCubes.as_view(), name='cubes'),
url(r'^reports/cube/(?P<cube_name>\S+)/model/$', CubeModel.as_view(), name='cube_model'),
url(r'^reports/cube/(?P<cube_name>\S+)/aggregate/$', CubeAggregation.as_view(), name='cube_aggregation'),
url(r'^reports/cube/(?P<cube_name>\S+)/cell/$', CubeCell.as_view(), name='cube_cell'),
url(r'^reports/cube/(?P<cube_name>\S+)/report/$', CubeReport.as_view(), name='cube_report'),
url(r'^reports/cube/(?P<cube_name>\S+)/facts/$', CubeFacts.as_view(), name='cube_facts'),
url(r'^reports/cube/(?P<cube_name>\S+)/fact/(?P<fact_id>\S+)/$', CubeFact.as_view(), name='cube_fact'),
url(r'^reports/cube/(?P<cube_name>\S+)/members/(?P<dimension_name>\S+)/$', CubeMembers.as_view(), name='cube_members'),
path('reports/dashboard/', views.cubes, name="dashboard"),
'''