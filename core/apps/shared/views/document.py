from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from core.apps.shared.serializers.document import DocuemntCreateSerializer, DocumentSerializer
from core.apps.shared.models import Document, DocumentResult
from payme.models import PaymeTransactions


class DocumentCreateView(GenericAPIView):
    serializer_class = DocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            document = serializer.save()
            return Response(
                {
                    "id": document.id,
                    "order_id": document.orders.first().id,
                    "total_price": document.total_price,
                    "discount": Decimal(41200) - document.total_price,
                }
            )
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class DocumentListApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            documents = Document.objects.filter(user=request.user)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)



class DocumentDetailApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            document = Document.objects.filter(user=request.user, id=id).first()
            if not document:
                return Response({'error': 'Document not found'}, status=404)
            order_id = document.orders.first().id
            payme_transaction = PaymeTransactions.objects.filter(account_id=order_id).first()
            if payme_transaction is None:
                return Response({'error': 'Payment not found'}, status=404)
            if payme_transaction.state != 2:
                return Response({'error': 'Payment not completed'}, status=400)

            document.save()
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
