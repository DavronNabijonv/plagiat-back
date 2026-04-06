from django.conf import settings

from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from core.apps.shared.serializers.ai_document import AiDocuemntCreateSerializer, AiDocumentSerializer
from core.apps.shared.models import AiDocument, AiDocumentResult, AiOrder
from payme.models import PaymeTransactions
from payme import Payme


class AiDocumentCreateView(GenericAPIView):
    serializer_class = AiDocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            ai_document = serializer.save()
            return Response(
                {
                    "id": ai_document.id,
                    "order_id": ai_document.ai_order.id,
                }
            )
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class AiDocumentListApiView(GenericAPIView):
    serializer_class = AiDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            ai_documents = AiDocument.objects.filter(user=request.user)
            serializer = self.get_serializer(ai_documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)



class AiDocumentDetailApiView(GenericAPIView):
    serializer_class = AiDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            document = AiDocument.objects.filter(user=request.user, id=id).first()
            if not document:
                return Response({'error': 'Document not found'}, status=404)
            order_id = document.ai_order.id
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



class PayForAiDocumentApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, document_id: int):
        try:
            document = AiDocument.objects.get(id=document_id, user=request.user)
        except AiDocument.DoesNotExist:
            return Response({"detail": "Hujjat topilmadi"}, status=404)

        payme = Payme(payme_id=settings.PAYME_ID)
        payment_link = payme.initializer.generate_pay_link(
            id=document.ai_order.id,
            amount=document.ai_order.total_price,
            return_url=f"https://anti-plagiat.uz/uz/{document.id}"
        )

        return Response({
            "order_id": document.ai_order.id,
            "payment_link": payment_link
        })
