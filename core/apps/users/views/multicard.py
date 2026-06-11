import hashlib
import hmac
from decimal import Decimal

from django.conf import settings
from django.db import transaction

import requests
from drf_spectacular.types import OpenApiTypes
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

from core.apps.shared.models.multicard_transaction import MulticardTransaction
from core.apps.shared.models.balance_topup import BalanceTopup
from core.apps.shared.models import Order


def _get_token() -> str:
    """
    POST /auth → JWT token oladi.
    Har so'rovda yangi token olinadi (token 24 soat amal qiladi).
    """
    resp = requests.post(
        f"{settings.MULTICARD_API_URL}/auth",
        json={
            "application_id": settings.MULTICARD_APPLICATION_ID,
            "secret": settings.MULTICARD_SECRET_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def _build_multicard_url(
    order_id, amount_tiyin, return_url, description
) -> tuple[str, str]:
    """
    POST /payment/invoice → checkout_url va invoice uuid qaytaradi.
    """
    token = _get_token()
    payload = {
        "store_id": settings.MULTICARD_STORE_ID,
        "amount": amount_tiyin,
        "invoice_id": str(order_id),
        "callback_url": settings.MULTICARD_CALLBACK_URL,
        "return_url": return_url,
        "lang": "uz",
    }
    resp = requests.post(
        f"{settings.MULTICARD_API_URL}/payment/invoice",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    checkout_url = data.get("checkout_url") or data.get("url")
    uuid = data.get("uuid") or str(order_id)
    return uuid, checkout_url


def _verify_signature(
    uuid: str, invoice_id: str, amount, sign: str
) -> bool:
    """SHA1({uuid}{invoice_id}{amount}{secret}) — Multicard webhook imzosi."""
    raw = f"{uuid}{invoice_id}{amount}{settings.MULTICARD_SECRET_KEY}"
    expected = hashlib.sha1(raw.encode()).hexdigest()
    return hmac.compare_digest(expected, sign)


class MulticardCreateView(APIView):
    """
    POST /api/v1/users/multicard/pay/<order_id>/
    Invoice yaratib, foydalanuvchini checkout_url ga yo'naltiradi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Multicard orqali order to'lash",
        description=(
            "Order uchun Multicard invoice yaratadi va checkout havolasini "
            "qaytaradi. Foydalanuvchini `payment_url` ga yo'naltiring — u yerda "
            "istalgan O'zbekiston kartasi (Uzcard/Humo, Payme/Click/Uzum) bilan "
            "to'lash mumkin.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "transaction_id": "uuid",\n'
            '  "payment_url": "https://checkout.multicard.uz/..."\n'
            "}\n"
            "```\n"
            "To'lov natijasi webhook orqali avtomatik qayd etiladi; holatni "
            "order/hujjat detail endpointlaridan tekshiring."
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
                    name='MulticardPayResponse',
                    fields={
                        'transaction_id': serializers.CharField(),
                        'payment_url': serializers.URLField(),
                    },
                ),
                description="Invoice yaratildi, checkout havolasi qaytarildi",
            ),
            400: OpenApiResponse(description="Order allaqachon balans orqali to'langan"),
            404: OpenApiResponse(description="Order topilmadi yoki sizga tegishli emas"),
            502: OpenApiResponse(description="Multicard bilan bog'lanishda xatolik"),
        },
    )
    def post(self, request, order_id):
        order = Order.objects.filter(
            id=order_id, user=request.user
        ).first()
        if not order:
            return Response(
                {"error": "Order topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.payment_provider == 'balance':
            return Response(
                {"error": "Bu order balans orqali to'langan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from core.apps.users.views.payme import _return_url
        try:
            uuid, checkout_url = _build_multicard_url(
                order_id=order.id,
                amount_tiyin=int(order.total_price * 100),
                return_url=_return_url(order),
                description=f"Anti-plagiat #{order.id}",
            )
        except Exception as e:
            return Response(
                {"error": f"Multicard xatoligi: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        MulticardTransaction.objects.update_or_create(
            order=order,
            defaults={
                "transaction_id": uuid,
                "amount": order.total_price,
                "state": MulticardTransaction.CREATED,
            },
        )
        order.payment_provider = 'multicard'
        order.save(update_fields=['payment_provider'])

        return Response({
            "transaction_id": uuid,
            "payment_url": checkout_url,
        })


class MulticardTopupCreateView(APIView):
    """
    POST /api/v1/users/multicard/topup/
    body: { "amount": 50000 }
    Balans to'ldirish uchun invoice yaratadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="Balansni to'ldirish (Multicard)",
        description=(
            "Foydalanuvchi ichki balansini to'ldirish uchun Multicard invoice "
            "yaratadi.\n\n"
            "**So'rov tanasi:**\n"
            "```json\n"
            '{ "amount": 50000 }\n'
            "```\n"
            "`amount` — so'mda, minimal **1000 so'm**.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "topup_id": 12,\n'
            '  "transaction_id": "uuid",\n'
            '  "payment_url": "https://checkout.multicard.uz/..."\n'
            "}\n"
            "```\n"
            "Foydalanuvchini `payment_url` ga yo'naltiring. To'lov tasdiqlangach "
            "balans avtomatik oshadi — yangi qiymatni `GET /users/balance/` dan oling."
        ),
        request=inline_serializer(
            name='MulticardTopupRequest',
            fields={
                'amount': serializers.IntegerField(
                    min_value=1000,
                    help_text="To'ldirish miqdori, so'mda (minimal 1000)",
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='MulticardTopupResponse',
                    fields={
                        'topup_id': serializers.IntegerField(),
                        'transaction_id': serializers.CharField(),
                        'payment_url': serializers.URLField(),
                    },
                ),
                description="Invoice yaratildi, checkout havolasi qaytarildi",
            ),
            400: OpenApiResponse(description="amount yuborilmagan yoki 1000 so'mdan kam"),
            502: OpenApiResponse(description="Multicard bilan bog'lanishda xatolik"),
        },
    )
    def post(self, request):
        amount = request.data.get('amount')
        if not amount or Decimal(str(amount)) < Decimal('1000'):
            return Response(
                {"error": "Minimal to'ldirish miqdori 1000 so'm"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        amount = Decimal(str(amount))

        topup = BalanceTopup.objects.create(
            user=request.user,
            amount=amount,
        )

        try:
            uuid, checkout_url = _build_multicard_url(
                order_id=f"topup_{topup.id}",
                amount_tiyin=int(amount * 100),
                return_url="https://anti-plagiat.uz/uz/balance",
                description=f"Balans to'ldirish #{topup.id}",
            )
        except Exception as e:
            topup.delete()
            return Response(
                {"error": f"Multicard xatoligi: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        MulticardTransaction.objects.create(
            topup=topup,
            transaction_id=uuid,
            amount=amount,
            state=MulticardTransaction.CREATED,
        )

        return Response({
            "topup_id": topup.id,
            "transaction_id": uuid,
            "payment_url": checkout_url,
        })


class MulticardWebhookView(APIView):
    """
    POST /payment/multicard/
    Multicard to'lov natijasini shu endpointga yuboradi (IP: 195.158.26.90).

    sign = SHA1(uuid + invoice_id + amount + secret)
    status 'success' → to'landi; 'error'|'revert' → bekor.
    Javob: {"success": true} HTTP 200 (aks holda 5 marta qayta urinadi).
    """
    permission_classes = []

    @extend_schema(
        tags=['Webhook'],
        summary="Multicard webhook (frontend uchun emas)",
        description=(
            "Multicard to'lov natijasini shu endpointga o'zi yuboradi. "
            "**Frontend bu endpointni chaqirmaydi.**"
        ),
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiResponse(description='{"success": true}')},
    )
    def post(self, request):
        data = request.data
        uuid = data.get('uuid', '')
        invoice_id = data.get('invoice_id', '')
        amount = data.get('amount', 0)
        sign = data.get('sign', '')
        evt_status = data.get('status', '')

        if not _verify_signature(uuid, invoice_id, amount, sign):
            return Response(
                {"success": False, "message": "Invalid signature"},
                status=status.HTTP_403_FORBIDDEN,
            )

        tx = MulticardTransaction.objects.filter(
            transaction_id=uuid
        ).first()
        if not tx:
            return Response({"success": True})

        if evt_status == 'success':
            self._handle_success(tx)
        elif evt_status in ('error', 'revert'):
            with transaction.atomic():
                tx.state = MulticardTransaction.CANCELLED
                tx.save(update_fields=['state', 'updated_at'])

        return Response({"success": True})

    @transaction.atomic
    def _handle_success(self, tx):
        if tx.state == MulticardTransaction.PAID:
            return

        tx.state = MulticardTransaction.PAID
        tx.save(update_fields=['state', 'updated_at'])

        if tx.topup_id:
            topup = (
                BalanceTopup.objects
                .select_for_update()
                .get(id=tx.topup_id)
            )
            if not topup.is_applied:
                topup.user.balance += topup.amount
                topup.user.save(update_fields=['balance'])
                topup.is_applied = True
                topup.save(update_fields=['is_applied', 'updated_at'])
