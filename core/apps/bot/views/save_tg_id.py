from django.db import transaction

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.apps.bot.serializers.save_tg_id import TelegramIdSerializer
from core.apps.users.models import User


class SaveTelegramIdView(GenericAPIView):
    serializer_class = TelegramIdSerializer
    queryset = User.objects.all()

    @transaction.atomic
    def post(self, request):
        try:
            serializer = TelegramIdSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                user = User.objects.get(phone=serializer.validated_data['phone'])
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=404)
            user.tg_id = serializer.validated_data['tg_id']
            user.save()
            return Response({'message': 'Telegram ID saved successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
