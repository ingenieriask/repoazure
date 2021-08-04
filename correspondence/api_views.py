from os import truncate
from django.http.response import HttpResponse
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from correspondence.serializers import RadicateSerializer,RadicateSerializerDetail,FilesSerializerDetail
from correspondence.models import AlfrescoFile, Radicate


class RadicatePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class RadicateList(ListAPIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Radicate.objects.all()
    serializer_class = RadicateSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id', 'subject', 'type')
    pagination_class = RadicatePagination


class RadicateDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self,radi_number):
        try:
            return Radicate.objects.get(number=radi_number)
        except:
            return HttpResponse(
                status=status.HTTP_404_NOT_FOUND)

    def get(self,request,radi_number):
        radicate = self.get_object(radi_number)
        serializer = RadicateSerializerDetail(radicate)
        return Response(serializer.data)


class FileDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self,radi_number):
        try:
            return AlfrescoFile.objects.filter(radicate__number=radi_number)
        except:
            return HttpResponse(
                status=status.HTTP_404_NOT_FOUND)

    def get(self,request,radi_number):
        file = self.get_object(radi_number)
        serializer = FilesSerializerDetail(file,many=True)
        return Response(serializer.data)

