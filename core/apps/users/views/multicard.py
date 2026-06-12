import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

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

from core.apps.shared.models import Order
from core.apps.shared.models.balance_topup import BalanceTopup
from core.apps.shared.models.multicard_transaction import MulticardTransaction
from core.services.raxmat import RaxmatError, RaxmatService

logger = logging.getLogger(__name__)


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
        order = Order.objects.filter(id=order_id, user=request.user).first()
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
            uuid, checkout_url = RaxmatService().create_invoice(
                amount=order.total_price,
                invoice_id=order.id,
                return_url=_return_url(order),
            )
        except RaxmatError as e:
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
        try:
            amount = Decimal(str(request.data.get('amount')))
        except (InvalidOperation, TypeError):
            amount = Decimal('0')
        if amount < Decimal('1000'):
            return Response(
                {"error": "Minimal to'ldirish miqdori 1000 so'm"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        topup = BalanceTopup.objects.create(user=request.user, amount=amount)

        try:
            uuid, checkout_url = RaxmatService().create_invoice(
                amount=amount,
                invoice_id=f"topup_{topup.id}",
                return_url="https://anti-plagiat.uz/uz/balance",
            )
        except RaxmatError as e:
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


class _MulticardCallbackBase(APIView):
    """Multicard'dan kelgan to'lov natijasini qayta ishlovchi bazaviy view.

    Imzo tekshiriladi, summa solishtiriladi, so'ng tranzaksiya holati
    yangilanadi. Multicard'ga {"success": true} + HTTP 200 qaytarilmasa,
    u callback'ni 5 martagacha qayta yuboradi — shu sababli "bizga
    tegishli emas" holatlarda ham 200 qaytariladi.
    """

    # Tashqi tizim chaqiradi — autentifikatsiya yo'q, himoya imzo orqali
    permission_classes = []
    authentication_classes = []

    # Log'larda success va webhook callback'larini farqlash uchun
    callback_kind = "callback"

    @extend_schema(
        tags=['Webhook'],
        summary="Multicard callback (frontend uchun emas)",
        description=(
            "Multicard to'lov natijasini shu endpointga o'zi yuboradi. "
            "**Frontend bu endpointni chaqirmaydi.**"
        ),
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiResponse(description='{"success": true}')},
    )
    def post(self, request):
        data = request.data
        service = RaxmatService()

        if not service.verify_callback_sign(data):
            logger.warning(
                "Multicard %s callback: imzo mos kelmadi (invoice_id=%s)",
                self.callback_kind, data.get("invoice_id"),
            )
            return Response(
                {"success": False, "message": "Invalid signature"},
                status=status.HTTP_403_FORBIDDEN,
            )

        tx = MulticardTransaction.objects.filter(
            transaction_id=data.get("uuid", "")
        ).first()
        if tx is None:
            # Bizda bunday tranzaksiya yo'q — baribir 200, aks holda
            # Multicard yo'q invoice uchun qayta urinaveradi
            logger.warning(
                "Multicard %s callback: tranzaksiya topilmadi (uuid=%s, invoice_id=%s)",
                self.callback_kind, data.get("uuid"), data.get("invoice_id"),
            )
            return Response({"success": True})

        # Multicard summani tiyinda yuboradi, bazada so'mda saqlanadi
        try:
            received_amount = Decimal(str(data.get("amount", 0)))
        except InvalidOperation:
            received_amount = Decimal("-1")
        if received_amount != tx.amount * 100:
            logger.warning(
                "Multicard %s callback: summa mos kelmadi "
                "(invoice_id=%s, kelgan=%s, kutilgan=%s)",
                self.callback_kind, data.get("invoice_id"),
                received_amount, tx.amount * 100,
            )
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

        evt_status = data.get("status", "")
        if evt_status == "success":
            self._apply_success(tx, data)
        elif evt_status in ("error", "revert"):
            self._apply_cancel(tx)
        # Boshqa statuslar (masalan, oraliq holatlar) — shunchaki qabul qilinadi

        return Response({"success": True})

    @extend_schema(exclude=True)
    def get(self, request):
        # Foydalanuvchi to'lovdan keyin brauzer orqali kelib qolsa
        return Response({"success": True}, status=status.HTTP_200_OK)

    @transaction.atomic
    def _apply_success(self, tx: MulticardTransaction, data: dict) -> None:
        # Qator bloklanadi: webhook va success callback bir vaqtda kelsa ham
        # to'lov faqat bir marta qayd etiladi (idempotentlik)
        tx = MulticardTransaction.objects.select_for_update().get(pk=tx.pk)
        if tx.state == MulticardTransaction.PAID:
            return

        payment_time = parse_datetime(str(data.get("payment_time") or ""))
        if payment_time and timezone.is_naive(payment_time):
            payment_time = timezone.make_aware(payment_time)

        tx.state = MulticardTransaction.PAID
        tx.payment_system = data.get("ps") or None
        tx.payment_time = payment_time
        tx.save(update_fields=[
            "state", "payment_system", "payment_time", "updated_at",
        ])

        # Balans to'ldirish bo'lsa — foydalanuvchi balansini oshiramiz.
        # Order to'lovi uchun qo'shimcha amal shart emas: serializer'lar
        # to'lov holatini tx.state orqali aniqlaydi.
        if tx.topup_id:
            topup = BalanceTopup.objects.select_for_update().get(id=tx.topup_id)
            if not topup.is_applied:
                topup.user.balance += topup.amount
                topup.user.save(update_fields=["balance"])
                topup.is_applied = True
                topup.save(update_fields=["is_applied", "updated_at"])

    def _apply_cancel(self, tx: MulticardTransaction) -> None:
        if tx.state == MulticardTransaction.PAID:
            # To'langan tranzaksiya 'revert' bo'lsa pulni avtomatik qaytarmaymiz —
            # bu holat qo'lda ko'rib chiqilishi kerak
            logger.warning(
                "Multicard %s callback: PAID tranzaksiyaga revert keldi (uuid=%s)",
                self.callback_kind, tx.transaction_id,
            )
            return
        tx.state = MulticardTransaction.CANCELLED
        tx.save(update_fields=["state", "updated_at"])


class MulticardWebhookCallbackView(_MulticardCallbackBase):
    """Multicard serveridan keladigan server-to-server webhook."""

    callback_kind = "webhook"


class MulticardSuccessCallbackView(_MulticardCallbackBase):
    """To'lov muvaffaqiyatli yakunlanganda keladigan success callback."""

    callback_kind = "success"
