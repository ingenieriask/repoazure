from django.http.response import HttpResponse
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from rest_framework import status

from rest_framework.response import Response
from correspondence.serializers import RadicateSerializer,RadicateSerializerDetail
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

class RadicateDetail(APIView):

    def get_object(self,radi_nuber):
        try:
            return Radicate.objects.get(number=radi_nuber)
        except:
            return HttpResponse(
                status=status.HTTP_404_NOT_FOUND)

    def get(self,request,radi_nuber):
        radicate = self.get_object(radi_nuber)
        serializer = RadicateSerializerDetail(radicate)
        return Response(serializer.data)

