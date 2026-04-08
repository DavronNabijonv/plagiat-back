from decimal import Decimal

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from drf_spectacular.utils import extend_schema

from core.apps.shared.serializers.document import DocuemntCreateSerializer, DocumentSerializer
from core.apps.shared.models import Document
from payme.models import PaymeTransactions

class DocumentCreateView(GenericAPIView):
    serializer_class = DocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['Document'])
    def post(self, request):
        serializer = DocuemntCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        document, order, discount_price = serializer.save()
        return Response(
            {
                "id": document.id,
                "order_id": order.id,
                "total_price": order.total_price,
                "discount": discount_price,
                "service_fee": order.total_price + Decimal(0.05),
            }
        )

class DocumentListApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['Document'])
    def get(self, request):
        documents = Document.objects.filter(user=request.user)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentDetailApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['Document'])
    def get(self, request, id):
        try:
            document = Document.objects.filter(user=request.user, id=id).first()
            if not document:
                return Response({'error': 'Document not found'}, status=404)
            order = document.orders.filter(type="document").first()
            order_id = order.id
            payme_transaction = PaymeTransactions.objects.filter(account_id=order_id).first()
            if payme_transaction is None:
                return Response({'error': 'Payment not found'}, status=404)
            if payme_transaction.state != 2:
                return Response({'error': 'Payment not completed'}, status=400)

            document.save()
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
