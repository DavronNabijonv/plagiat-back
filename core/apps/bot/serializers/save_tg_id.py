from rest_framework import serializers

class TelegramIdSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=True)
    tg_id = serializers.CharField(max_length=200, required=True)
