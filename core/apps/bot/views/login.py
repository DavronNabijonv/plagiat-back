from django.db import transaction

from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.bot.serializers.login import BotLoginSerializer
from core.apps.users.models import User


class LoginView(GenericAPIView):
    serializer_class = BotLoginSerializer
    queryset = User.objects.all()

    @transaction.atomic
    def post(self, request):
        try:
            serializer = BotLoginSerializer(data=request.data)
            if serializer.is_valid():
                tg_id = serializer.validated_data['tg_id']
                try:
                    user = User.objects.get(tg_id=tg_id)
                except User.DoesNotExist:
                    return Response({'message': 'User not found'}, status=404)

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                return Response({'message': 'User logged in successfully', 'access_token': access_token, 'refresh_token': refresh_token})
            else:
                return Response({'message': 'User login failed', 'error': serializer.errors}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
