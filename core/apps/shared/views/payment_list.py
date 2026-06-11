from itertools import chain
from operator import attrgetter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from core.apps.shared.models import Order
from core.apps.shared.serializers.payment_list import UnifiedOrderSerializer


class UnifiedOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Order'],
        summary="To'lovlar tarixi (barcha orderlar, yangi → eski)",
        description=(
            "Joriy foydalanuvchining barcha orderlarini to'lov holati bilan "
            "birga, yaratilgan vaqti bo'yicha kamayish tartibida qaytaradi. "
            "To'lovlar tarixi sahifasi uchun mo'ljallangan."
        ),
        responses={200: UnifiedOrderSerializer(many=True)},
    )
    def get(self, request):
        user = request.user

        orders = Order.objects.filter(user=user)

        combined = sorted(
            chain(orders),
            key=attrgetter('created_at'),
            reverse=True
        )

        serializer = UnifiedOrderSerializer(combined, many=True)
        return Response(serializer.data)
