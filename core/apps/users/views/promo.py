from decimal import Decimal

from django.db import transaction

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.models import Order
from core.apps.shared.models.promo_code import PromoCode, PromoUsage


class PromoApplyView(APIView):
    """
    POST /api/v1/users/promo/apply/<order_id>/   { "code": "PROMO2026" }

    BE-09: promo-kodni unpaid orderga qo'llaydi — narx foizga kamayadi.
    Frontend PaymentModal'dagi promo maydoni shu endpointni chaqiradi
    (FEATURES.PROMO_CODE flagi bilan yoqiladi).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Promo-kodni qo'llash",
        description=(
            "Faol va muddati o'tmagan promo-kodni to'lanmagan orderga "
            "qo'llaydi. Bitta orderga faqat bitta kod qo'llanadi.\n\n"
            "**Muvaffaqiyatli javob (200):**\n"
            "```json\n"
            "{\n"
            '  "success": true,\n'
            '  "code": "PROMO2026",\n'
            '  "discount_percent": 10,\n'
            '  "discount_amount": "2060.00",\n'
            '  "total_price": "18540.00"\n'
            "}\n"
            "```"
        ),
        parameters=[
            OpenApiParameter(
                name='order_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Chegirma qo'llanadigan order",
            ),
        ],
        request=inline_serializer(
            name='PromoApplyRequest',
            fields={'code': serializers.CharField()},
        ),
        responses={
            200: OpenApiResponse(description="Chegirma qo'llandi, yangi narx qaytadi"),
            400: OpenApiResponse(description="Kod noto'g'ri/muddati o'tgan yoki order to'langan/kod allaqachon qo'llangan"),
            404: OpenApiResponse(description="Order topilmadi"),
        },
    )
    @transaction.atomic
    def post(self, request, order_id: int):
        from core.apps.shared.serializers.payment_list import resolve_order_state

        code = str(request.data.get('code', '')).strip().upper()
        if not code:
            return Response(
                {"error": "code maydoni yuborilmadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = (
            Order.objects
            .select_for_update()
            .filter(id=order_id, user=request.user)
            .first()
        )
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

        if PromoUsage.objects.filter(order=order).exists():
            return Response(
                {"error": "Bu orderga promo-kod allaqachon qo'llangan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        promo = (
            PromoCode.objects
            .select_for_update()
            .filter(code__iexact=code)
            .first()
        )
        if not promo or not promo.is_valid():
            return Response(
                {"error": "Promo-kod noto'g'ri yoki muddati tugagan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        discount_amount = (
            order.total_price * Decimal(promo.discount_percent) / Decimal(100)
        ).quantize(Decimal('0.01'))
        order.total_price -= discount_amount
        order.save(update_fields=['total_price'])

        promo.used_count += 1
        promo.save(update_fields=['used_count'])

        PromoUsage.objects.create(
            promo=promo,
            order=order,
            user=request.user,
            discount_amount=discount_amount,
        )

        return Response({
            "success": True,
            "code": promo.code,
            "discount_percent": promo.discount_percent,
            "discount_amount": str(discount_amount),
            "total_price": str(order.total_price),
        })
