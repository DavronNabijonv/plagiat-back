from itertools import chain
from operator import attrgetter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.apps.shared.models import Order, AiOrder
from core.apps.shared.serializers.payment_list import UnifiedOrderSerializer


class UnifiedOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        orders = Order.objects.filter(user=user)
        ai_orders = AiOrder.objects.filter(user=user)

        combined = sorted(
            chain(orders, ai_orders),
            key=attrgetter('created_at'),
            reverse=True
        )

        serializer = UnifiedOrderSerializer(combined, many=True)
        return Response(serializer.data)
