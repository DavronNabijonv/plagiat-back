from rest_framework import serializers

from core.apps.users.models import User


class BotUserSerializer(serializers.Serializer):
    tg_id = serializers.CharField(max_length=200)
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200, required=False)
    phone = serializers.CharField(max_length=200, null=True, blank=True)