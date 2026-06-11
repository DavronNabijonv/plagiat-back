from decimal import Decimal

from django.db import transaction

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from core.apps.shared.models import Order
from core.apps.users.models import User


class PayWithBalanceView(APIView):
    """
    POST /api/v1/users/balance/pay/<order_id>/

    Foydalanuvchi balansi yetarli bo'lsa — ayni zahoti order ni to'langan
    deb belgilab, balansdan ayiradi. Tashqi API kerak emas.

    Nega select_for_update:
    Bir vaqtda kelgan ikki so'rov bir xil balansni ikki marta kamaytirmasligi
    uchun satr darajasida qulf qo'yamiz (PostgreSQL row-level lock).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Balansdan to'lash",
        description=(
            "Order narxini foydalanuvchining ichki balansidan yechib, orderni "
            "to'langan deb belgilaydi. Tashqi to'lov sahifasiga yo'naltirish "
            "kerak emas — natija darhol qaytadi.\n\n"
            "**Muvaffaqiyatli javob (200):**\n"
            "```json\n"
            "{\n"
            '  "success": true,\n'
            '  "order_id": 5,\n'
            '  "paid_amount": "41200.00",\n'
            '  "balance_left": "8800.00"\n'
            "}\n"
            "```\n"
            "**Balans yetarli bo'lmasa (402):**\n"
            "```json\n"
            "{\n"
            '  "error": "Balans yetarli emas",\n'
            '  "balance": "10000.00",\n'
            '  "required": "41200.00",\n'
            '  "difference": "31200.00"\n'
            "}\n"
            "```\n"
            "Bu holda foydalanuvchiga balansni to'ldirishni "
            "(`POST /users/multicard/topup/`) taklif qiling."
        ),
        parameters=[
            OpenApiParameter(
                name='order_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="To'lanadigan order ID si",
            ),
        ],
        request=None,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='PayWithBalanceResponse',
                    fields={
                        'success': serializers.BooleanField(),
                        'order_id': serializers.IntegerField(),
                        'paid_amount': serializers.CharField(),
                        'balance_left': serializers.CharField(),
                    },
                ),
                description="To'lov muvaffaqiyatli, qolgan balans qaytariladi",
            ),
            400: OpenApiResponse(description="Order allaqachon balansdan to'langan"),
            402: OpenApiResponse(description="Balans yetarli emas"),
            404: OpenApiResponse(description="Order topilmadi yoki sizga tegishli emas"),
        },
    )
    @transaction.atomic
    def post(self, request, order_id):
        user = (
            User.objects
            .select_for_update()
            .get(id=request.user.id)
        )
        order = Order.objects.filter(
            id=order_id, user=user
        ).first()

        if not order:
            return Response(
                {"error": "Order topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Allaqachon to'langan bo'lsa qayta to'latmaymiz
        if order.payment_provider == 'balance':
            return Response(
                {"error": "Bu order allaqachon balansdan to'langan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.balance < order.total_price:
            return Response(
                {
                    "error": "Balans yetarli emas",
                    "balance":    str(user.balance),
                    "required":   str(order.total_price),
                    "difference": str(order.total_price - user.balance),
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        user.balance -= order.total_price
        user.save(update_fields=['balance'])

        order.payment_provider = 'balance'
        order.save(update_fields=['payment_provider'])

        return Response({
            "success":       True,
            "order_id":      order.id,
            "paid_amount":   str(order.total_price),
            "balance_left":  str(user.balance),
        })


class BalanceView(APIView):
    """
    GET /api/v1/users/balance/
    Foydalanuvchining joriy balansini va to'ldirish tarixini qaytaradi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Joriy balans va to'ldirish tarixi",
        description=(
            "Foydalanuvchining joriy balansini va oxirgi 20 ta muvaffaqiyatli "
            "to'ldirish yozuvini qaytaradi.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "balance": "50000.00",\n'
            '  "topup_history": [\n'
            '    { "amount": "50000.00", "created_at": "2026-06-11T10:00:00Z" }\n'
            "  ]\n"
            "}\n"
            "```"
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='BalanceResponse',
                    fields={
                        'balance': serializers.CharField(),
                        'topup_history': inline_serializer(
                            name='BalanceTopupHistoryItem',
                            fields={
                                'amount': serializers.CharField(),
                                'created_at': serializers.DateTimeField(),
                            },
                            many=True,
                        ),
                    },
                ),
                description="Balans va to'ldirish tarixi",
            ),
        },
    )
    def get(self, request):
        from core.apps.shared.models.balance_topup import BalanceTopup

        topups = BalanceTopup.objects.filter(
            user=request.user, is_applied=True
        ).order_by('-created_at')[:20]

        history = [
            {
                "amount":     str(t.amount),
                "created_at": t.created_at,
            }
            for t in topups
        ]

        return Response({
            "balance": str(request.user.balance),
            "topup_history": history,
        })
