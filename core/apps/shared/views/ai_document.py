from django.conf import settings

from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.serializers.ai_document import AiDocuemntCreateSerializer, AiDocumentSerializer
from core.apps.shared.models import AiDocument, AiDocumentResult
from payme.models import PaymeTransactions
from payme import Payme


class AiDocumentCreateView(GenericAPIView):
    serializer_class = AiDocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['AI Document'],
        summary="Hujjatni AI detektor tekshiruviga yuborish",
        description=(
            "Matn AI (sun'iy intellekt) tomonidan yozilganligini aniqlash uchun "
            "hujjat yaratadi va to'lov orderini ochadi. So'rov "
            "`multipart/form-data` formatida yuboriladi.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            '{ "id": 7, "order_id": 31 }\n'
            "```\n"
            "Keyingi qadam: `order_id` bilan to'lov havolasini oling — "
            "`POST /users/payment/link/<order_id>/`. Natija to'lovdan so'ng "
            "`GET /shared/ai_document/<id>/` da ochiladi."
        ),
        responses={
            200: OpenApiResponse(description="AI hujjat va order yaratildi"),
            500: OpenApiResponse(description="Validatsiya yoki server xatosi"),
        },
    )
    def post(self, request):
        try:
            serializer = AiDocuemntCreateSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            ai_document, order = serializer.save()
            return Response(
                {
                    "id": ai_document.id,
                    "order_id": order.id,
                }
            )
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class AiDocumentListApiView(GenericAPIView):
    serializer_class = AiDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['AI Document'],
        summary="Mening AI hujjatlarim ro'yxati",
        description=(
            "Joriy foydalanuvchining barcha AI-detektor hujjatlarini qaytaradi. "
            "Faqat o'z hujjatlari ko'rinadi."
        ),
    )
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

    @extend_schema(
        tags=['AI Document'],
        summary="Bitta AI hujjat tafsilotlari (to'lovdan keyin)",
        description=(
            "AI hujjatning to'liq ma'lumotini va AI-detektor natijasini "
            "qaytaradi. **Natija faqat order to'langandan keyin ochiladi.**\n\n"
            "**Xato javoblari:**\n"
            "- `404 {\"error\": \"Document not found\"}` — hujjat topilmadi\n"
            "- `404 {\"error\": \"Payment not found\"}` — to'lov boshlanmagan\n"
            "- `400 {\"error\": \"Payment not completed\"}` — to'lov tugallanmagan"
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description="AI hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="AI hujjat va detektor natijasi"),
            400: OpenApiResponse(description="To'lov hali tugallanmagan"),
            404: OpenApiResponse(description="Hujjat yoki to'lov topilmadi"),
        },
    )
    def get(self, request, id):
        try:
            document = AiDocument.objects.filter(user=request.user, id=id).first()
            if not document:
                return Response({'error': 'Document not found'}, status=404)
            order_id = document.orders.filter(type="ai_document").first().id
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

    @extend_schema(
        tags=['AI Document'],
        summary="AI hujjat uchun Payme havolasi (hozir ishlatilmaydi)",
        description=(
            "AI hujjat orderiga to'g'ridan-to'g'ri Payme to'lov havolasini "
            "yaratadi. URL'da o'chirilgan — to'lov uchun "
            "`POST /users/payment/link/<order_id>/` dan foydalaning."
        ),
        deprecated=True,
    )
    def post(self, request, id: int):
        try:
            document = AiDocument.objects.get(id=id, user=request.user)
        except AiDocument.DoesNotExist:
            return Response({"detail": "Hujjat topilmadi"}, status=404)

        payme = Payme(payme_id=settings.PAYME_ID)
        payment_link = payme.initializer.generate_pay_link(
            id=document.orders.filter(type="ai_document").first().id,
            amount=document.orders.filter(type="ai_document").first().total_price,
            return_url=f"https://anti-plagiat.uz/uz/si/{document.id}"
        )

        return Response({
            "order_id": document.orders.filter(type="ai_document").first().id,
            "payment_link": payment_link
        })
