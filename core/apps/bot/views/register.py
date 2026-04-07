from django.db import transaction

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.bot.serializers.register import BotRegisterSerializer
from core.apps.users.models import User


class RegisterView(GenericAPIView):
    serializer_class = BotRegisterSerializer
    queryset = User.objects.all()

    @transaction.atomic
    def post(self, request):
        try:
            serializer = BotRegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                return Response({'message': 'User registered successfully', 'access_token': access_token, 'refresh_token': refresh_token})
            else:
                return Response({'message': 'User registration failed', 'error': serializer.errors}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
