from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination

from correspondence.serializers import RadicateSerializer
from correspondence.models import Radicate


class RadicatePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class RadicateList(ListAPIView):
    queryset = Radicate.objects.all()
    serializer_class = RadicateSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id', 'subject', 'type')
    pagination_class = RadicatePagination
