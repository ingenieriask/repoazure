from rest_framework import serializers
from correspondence.models import Radicate


class RadicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Radicate
        fields = ('id', 'number', 'date_radicated', 'type', 'subject')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
