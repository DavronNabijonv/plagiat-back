from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from core.apps.shared.models import Order
from core.apps.shared.serializers.order import OrderSerializer

class OrderListApiView(GenericAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            documents = Order.objects.filter(user=request.user)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
