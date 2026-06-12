from decimal import Decimal

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.serializers.document import DocuemntCreateSerializer, DocumentSerializer
from core.apps.shared.serializers.payment_list import resolve_order_state
from core.apps.shared.models import Document

class DocumentCreateView(GenericAPIView):
    serializer_class = DocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Document'],
        summary="Hujjatni plagiat tekshiruviga yuborish",
        description=(
            "Hujjat yaratadi va unga bog'liq to'lov orderini ochadi. "
            "So'rov `multipart/form-data` formatida yuboriladi.\n\n"
            "**So'rov maydonlari:**\n"
            "- `title` — hujjat nomi\n"
            "- `file` — tekshiriladigan fayl (PDF/DOCX va h.k.)\n"
            "- `certificate` — `true` bo'lsa sertifikat ham buyurtma qilinadi "
            "(narxga 20 600 so'm qo'shiladi)\n"
            "- `type` — hujjat turi ID si (`GET /shared/documents/types/` dan olinadi)\n"
            "- `text` — ixtiyoriy, fayl o'rniga matn\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "id": 10,\n'
            '  "order_id": 25,\n'
            '  "total_price": "41200.00",\n'
            '  "discount": "0.00",\n'
            '  "service_fee": "41200.00",\n'
            '  "certificate": "20600"\n'
            "}\n"
            "```\n"
            "Keyingi qadam: `order_id` bilan to'lov havolasini oling — "
            "`POST /users/payment/link/<order_id>/`. Tekshiruv natijasi to'lovdan "
            "so'ng `GET /shared/documents/<id>/` da ko'rinadi.\n\n"
            "Eslatma: bir oyda 10+ to'langan order bo'lsa 15% chegirma qo'llanadi."
        ),
        responses={
            200: OpenApiResponse(description="Hujjat va order yaratildi"),
            400: OpenApiResponse(description="Validatsiya xatosi (fayl yoki maydonlar noto'g'ri)"),
        },
    )
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
                "discount": order.total_price - discount_price,
                "service_fee": order.total_price,
                "certificate": Decimal(20600) if document.certificate else Decimal(0),
                # BE-07: AI-tekshiruv komponenti
                "ai_check": Decimal(10300) if document.ai_check else Decimal(0),
            }
        )

class DocumentListApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Document'],
        summary="Mening hujjatlarim ro'yxati",
        description=(
            "Joriy foydalanuvchining barcha plagiat-tekshiruv hujjatlarini "
            "qaytaradi (plagiat foizi, sertifikat holati va boshqa maydonlar "
            "bilan). Faqat o'z hujjatlari ko'rinadi."
        ),
    )
    def get(self, request):
        documents = Document.objects.filter(user=request.user)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentDetailApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Document'],
        summary="Bitta hujjat tafsilotlari (pay-to-unlock)",
        description=(
            "Hujjat ma'lumotini qaytaradi. **To'liq natija (results) faqat "
            "order to'langandan keyin ochiladi** — server tomonda himoya "
            "(BE-01).\n\n"
            "To'lanmagan hujjat uchun `state: \"unpaid\"`, `order_id` va "
            "`price_calculation` qaytadi, lekin `results` bo'sh bo'ladi — "
            "frontend teaser/lock ko'rinishini shu javobdan quradi.\n\n"
            "To'lov holati barcha providerlar (Payme, Multicard, balans, "
            "karta o'tkazmasi) bo'yicha tekshiriladi."
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Hujjat (to'langan bo'lsa natija bilan)"),
            404: OpenApiResponse(description="Hujjat topilmadi"),
        },
    )
    def get(self, request, id):
        document = Document.objects.filter(user=request.user, id=id).first()
        if not document:
            return Response({'error': 'Document not found'}, status=404)

        order = document.orders.filter(type="document").first()
        state = resolve_order_state(order) if order else 'unpaid'

        data = DocumentSerializer(document).data
        if state != 'paid':
            # Pay-to-unlock: natija server tomonda yashiriladi (BE-01)
            data['results'] = []
        return Response(data)
