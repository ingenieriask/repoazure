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
    path('/cube/<str:cube_name>/facts/', CubeFacts.as_view(), name="cube_facts"),
    path('cube/<str:cube_name>/fact/<str:fact_id>/', CubeFact.as_view(), name="cube_fact"),
    path('cube/<str:cube_name>/members/<str:dimension_name>/', CubeMembers.as_view(), name="cube_members"),
    path('/cube/<str:cube_name>/members/<str:dimension_name>/', CubeMembers.as_view(), name="cube_members"),
    path('dashboard/', views.cubes, name="dashboard"),
]
