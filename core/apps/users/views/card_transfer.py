from decimal import Decimal

from django.db import transaction

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.models import Order
from core.apps.shared.models.card_transfer import CardRequisite, CardTransferPayment


class CardRequisitesView(APIView):
    """
    GET /api/v1/users/card/requisites/

    BE-22/23: faol karta rekvizitlari ro'yxati. `order_id` query param
    berilsa har bir davlat valyutasida to'lanadigan summa ham hisoblanadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Karta o'tkazmasi rekvizitlari (davlat/valyuta bo'yicha)",
        description=(
            "Karta orqali to'lov uchun faol rekvizitlar ro'yxati. "
            "`?order_id=<id>` berilsa, javobdagi `local_amount` — order narxi "
            "mahalliy valyutaga kurs bo'yicha hisoblangan summa."
        ),
        parameters=[
            OpenApiParameter(
                name='order_id',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Narxi konvertatsiya qilinadigan order",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='CardRequisiteItem',
                    fields={
                        'id': serializers.IntegerField(),
                        'country': serializers.CharField(),
                        'country_code': serializers.CharField(),
                        'currency': serializers.CharField(),
                        'card_number': serializers.CharField(),
                        'card_holder': serializers.CharField(),
                        'bank_name': serializers.CharField(allow_null=True),
                        'local_amount': serializers.FloatField(allow_null=True),
                    },
                    many=True,
                ),
                description="Faol rekvizitlar",
            ),
        },
    )
    def get(self, request):
        order_price = None
        order_id = request.query_params.get('order_id')
        if order_id:
            order = Order.objects.filter(id=order_id, user=request.user).first()
            if order:
                order_price = order.total_price

        items = []
        for r in CardRequisite.objects.filter(is_active=True):
            local_amount = None
            if order_price is not None:
                local_amount = float(
                    (order_price * r.exchange_rate).quantize(Decimal('0.01'))
                )
            items.append({
                'id': r.id,
                'country': r.country,
                'country_code': r.country_code,
                'currency': r.currency,
                'card_number': r.card_number,
                'card_holder': r.card_holder,
                'bank_name': r.bank_name,
                'local_amount': local_amount,
            })
        return Response(items)


class CardReceiptUploadView(APIView):
    """
    POST /api/v1/users/card/receipt/<order_id>/

    BE-24: foydalanuvchi o'tkazma chekini yuklaydi, to'lov
    "tasdiq kutilmoqda" holatiga o'tadi. Frontend PaymentModal
    aynan shu endpointga `receipt` faylini yuboradi.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=['Payment'],
        summary="Karta o'tkazmasi chekini yuklash",
        description=(
            "Multipart so'rov:\n"
            "- `receipt` — chek rasmi yoki PDF (majburiy)\n"
            "- `requisite_id` — qaysi kartaga to'langani (ixtiyoriy)\n"
            "- `amount` — to'langan summa, mahalliy valyutada (ixtiyoriy)\n\n"
            "Muvaffaqiyatda to'lov `pending` (tasdiq kutilmoqda) bo'ladi; "
            "admin tasdiqlagach `GET /shared/documents/<id>/` da natija ochiladi "
            "va foydalanuvchiga Telegram orqali xabar boradi (tg_id bo'lsa)."
        ),
        parameters=[
            OpenApiParameter(
                name='order_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="To'lanayotgan order ID si",
            ),
        ],
        request=inline_serializer(
            name='CardReceiptUploadRequest',
            fields={
                'receipt': serializers.FileField(),
                'requisite_id': serializers.IntegerField(required=False),
                'amount': serializers.DecimalField(
                    max_digits=15, decimal_places=2, required=False
                ),
            },
        ),
        responses={
            201: OpenApiResponse(description="Chek qabul qilindi — tasdiq kutilmoqda"),
            400: OpenApiResponse(description="Chek fayli yuborilmagan yoki order allaqachon to'langan"),
            404: OpenApiResponse(description="Order topilmadi"),
        },
    )
    @transaction.atomic
    def post(self, request, order_id: int):
        from core.apps.shared.serializers.payment_list import resolve_order_state

        order = Order.objects.filter(id=order_id, user=request.user).first()
        if not order:
            return Response(
                {"error": "Order topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if resolve_order_state(order) == 'paid':
            return Response(
                {"error": "Bu order allaqachon to'langan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        receipt = request.FILES.get('receipt')
        if not receipt:
            return Response(
                {"error": "receipt fayli yuborilmadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requisite = None
        requisite_id = request.data.get('requisite_id')
        if requisite_id:
            requisite = CardRequisite.objects.filter(id=requisite_id).first()

        payment = CardTransferPayment.objects.create(
            order=order,
            user=request.user,
            requisite=requisite,
            receipt=receipt,
            amount=request.data.get('amount') or None,
            currency=requisite.currency if requisite else 'UZS',
        )

        order.payment_provider = 'card_transfer'
        order.save(update_fields=['payment_provider'])

        return Response(
            {
                "success": True,
                "payment_id": payment.id,
                "state": payment.state,
                "message": "Chek qabul qilindi — tasdiq kutilmoqda",
            },
            status=status.HTTP_201_CREATED,
        )
