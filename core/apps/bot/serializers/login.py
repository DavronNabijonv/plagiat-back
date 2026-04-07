from rest_framework import serializers

class BotLoginSerializer(serializers.Serializer):
    tg_id = serializers.CharField()
