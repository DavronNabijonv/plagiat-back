from rest_framework import serializers

from core.apps.users.models import User


class BotRegisterSerializer(serializers.Serializer):
    tg_id = serializers.CharField()
    phone = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField()

    def validate_tg_id(self, value):
        if User.objects.filter(tg_id=value).exists():
            raise serializers.ValidationError("Telegram ID already exists")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def create(self, validated_data):
        user = User.objects.create(
            tg_id=validated_data['tg_id'],
            phone=validated_data['phone'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user
