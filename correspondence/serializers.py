from correspondence.ecm_services import ECMService
from django.db import models
from rest_framework import serializers
from correspondence.models import Radicate,AlfrescoFile


class RadicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Radicate
        fields = ('id', 'number', 'date_radicated', 'type', 'subject')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data



class RadicateSerializerDetail(serializers.ModelSerializer):
    reported_people = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
     )
    class Meta:
        model = Radicate
        fields = (
            'id', 'number', 'date_radicated',
            'annexes','type', 'subject','observation',
            'data','date_radicated','creator',
            'record','person','current_user',
            'last_user','reception_mode','use_parent_address',
            'office','d(octype','parent','mother',
            'classification','folder_id','status','reported_people',
            'is_filed','email_user_email','email_user_name',
            'stage'
            )

class FilesSerializerDetail(serializers.ModelSerializer):

    url_file = serializers.SerializerMethodField()
    class Meta:
        model= AlfrescoFile
        fields=(
            'radicate','size','name',
            'extension','request','url_file','cmis_id'
        )
    def get_url_file(self,obj):
        return str(ECMService.download(obj.cmis_id))