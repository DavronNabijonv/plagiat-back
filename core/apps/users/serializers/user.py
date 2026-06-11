from rest_framework import serializers

from core.apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone',
            'balance',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'balance':  {'read_only': True},
        }

    def validate_phone(self, phone):
        user = (
            User.objects
            .filter(phone=phone)
            .exclude(id=self.instance.id)
            .first()
        )
        if user:
            raise serializers.ValidationError("Phone number already exists")
        return phone

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get(
            'first_name', instance.first_name
        )
        instance.last_name = validated_data.get(
            'last_name', instance.last_name
        )
        instance.phone = validated_data.get('phone', instance.phone)
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        return instance
