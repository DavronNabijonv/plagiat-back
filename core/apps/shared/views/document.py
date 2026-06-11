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
from core.apps.shared.models import Document
from payme.models import PaymeTransactions

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
        summary="Bitta hujjat tafsilotlari (to'lovdan keyin)",
        description=(
            "Hujjatning to'liq ma'lumotini, jumladan plagiat tekshiruv "
            "natijasini qaytaradi. **Natija faqat order to'langandan keyin "
            "ochiladi** — aks holda 400/404 xato qaytadi.\n\n"
            "**Xato javoblari:**\n"
            "- `404 {\"error\": \"Document not found\"}` — hujjat topilmadi\n"
            "- `404 {\"error\": \"Payment not found\"}` — to'lov boshlanmagan\n"
            "- `400 {\"error\": \"Payment not completed\"}` — to'lov tugallanmagan\n\n"
            "To'lov tugallanmagan bo'lsa foydalanuvchini to'lov havolasiga "
            "qaytaring (`POST /users/payment/link/<order_id>/`)."
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
            200: OpenApiResponse(description="Hujjat va plagiat natijasi"),
            400: OpenApiResponse(description="To'lov hali tugallanmagan"),
            404: OpenApiResponse(description="Hujjat yoki to'lov topilmadi"),
        },
    )
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
