from rest_framework import serializers


class CheckFileSerializer(serializers.Serializer):
    file = serializers.FileField()
