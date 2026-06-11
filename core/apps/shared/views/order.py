from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from drf_spectacular.utils import extend_schema

from core.apps.shared.models import Order
from core.apps.shared.serializers.order import OrderSerializer

class OrderListApiView(GenericAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Order'],
        summary="Mening orderlarim ro'yxati",
        description=(
            "Joriy foydalanuvchining barcha to'lov orderlarini qaytaradi "
            "(type: `document`, `ai_document` yoki `certificate`). "
            "Faqat o'z orderlari ko'rinadi."
        ),
    )
    def get(self, request):
        try:
            documents = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
