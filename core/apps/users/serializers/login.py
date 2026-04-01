from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        data['user_id'] = user.id
        data['phone'] = user.phone
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        return data
