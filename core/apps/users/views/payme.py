from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from payme.views import PaymeWebHookAPIView

from core.apps.shared.models import Order
from core.apps.shared.models.multicard_transaction import MulticardTransaction
from core.services.raxmat import RaxmatError, RaxmatService


def _return_url(order: Order) -> str:
    if order.type == "ai_document":
        return f"https://anti-plagiat.uz/uz/si/{order.ai_document_id}"
    if order.document_id:
        return f"https://anti-plagiat.uz/uz/{order.document_id}"
    return "https://anti-plagiat.uz"


@extend_schema(
    tags=['Webhook'],
    summary="Payme webhook (frontend uchun emas)",
    description=(
        "Payme to'lov tizimi to'lov holati o'zgarganda shu endpointga o'zi "
        "so'rov yuboradi. **Frontend bu endpointni chaqirmaydi.**"
    ),
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)
class PaymeCallBackAPIView(PaymeWebHookAPIView):
    def handle_successfully_payment(self, params, result, *args, **kwargs):
        print(f"Payme to'lov muvaffaqiyatli: {params}")

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        print(f"Payme to'lov bekor qilindi: {params}")


class PaymentLinkView(APIView):
    """
    POST /api/v1/users/payment/link/<order_id>/
    body: { "method": "multicard" | "balance" }

    Multicard hamma provayderlarni (Payme/Click/Uzum) o'zida birlashtiradi.
    'balance' tanlansa /users/balance/pay/<order_id>/ ga yo'naltiriladi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payment'],
        summary="To'lov havolasini olish (yagona entry point)",
        description=(
            "Order uchun to'lov havolasini yaratadi. Frontend to'lov uchun "
            "**faqat shu endpointni** ishlatishi tavsiya etiladi.\n\n"
            "**So'rov tanasi:**\n"
            "```json\n"
            '{ "method": "multicard" }\n'
            "```\n"
            "- `method: \"multicard\"` (default) — Multicard checkout sahifasi havolasi "
            "qaytariladi (Payme/Click/Uzum kartalarining barchasini qabul qiladi)\n"
            "- `method: \"balance\"` — ichki balansdan to'lashga yo'naltiriladi\n\n"
            "**Javob (multicard):**\n"
            "```json\n"
            "{\n"
            '  "transaction_id": "uuid",\n'
            '  "payment_url": "https://checkout.multicard.uz/...",\n'
            '  "method": "multicard"\n'
            "}\n"
            "```\n"
            "Foydalanuvchini `payment_url` ga yo'naltiring; to'lovdan so'ng u saytga "
            "qaytariladi.\n\n"
            "**Javob (balance):**\n"
            "```json\n"
            '{ "redirect": "balance", "url": "/api/v1/users/balance/pay/<order_id>/" }\n'
            "```\n"
            "Bu holda ko'rsatilgan `url` ga POST yuborib balansdan to'lang."
        ),
        parameters=[
            OpenApiParameter(
                name='order_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="To'lanadigan order ID si (hujjat yaratishda qaytariladi)",
            ),
        ],
        request=inline_serializer(
            name='PaymentLinkRequest',
            fields={
                'method': serializers.ChoiceField(
                    choices=['multicard', 'balance'],
                    required=False,
                    default='multicard',
                    help_text="To'lov usuli. Berilmasa 'multicard' olinadi.",
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='PaymentLinkResponse',
                    fields={
                        'transaction_id': serializers.CharField(required=False),
                        'payment_url': serializers.URLField(required=False),
                        'method': serializers.CharField(required=False),
                        'redirect': serializers.CharField(required=False),
                        'url': serializers.CharField(required=False),
                    },
                ),
                description="To'lov havolasi (multicard) yoki balans yo'naltirishi",
            ),
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

        method = request.data.get('method', 'multicard')
        if method == 'balance':
            return Response({
                "redirect": "balance",
                "url": f"/api/v1/users/balance/pay/{order_id}/",
            })

        try:
            trans_id, pay_url = RaxmatService().create_invoice(
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
                "transaction_id": trans_id,
                "amount":         order.total_price,
                "state":          MulticardTransaction.CREATED,
            },
        )
        order.payment_provider = 'multicard'
        order.save(update_fields=['payment_provider'])

        return Response({
            "transaction_id": trans_id,
            "payment_url":    pay_url,
            "method":         "multicard",
        })


# Orqaga moslik uchun
@extend_schema_view(
    post=extend_schema(
        tags=['Payment'],
        summary="To'lov havolasi (eski yo'l, deprecated)",
        description=(
            "`/users/payment/link/<order_id>/` bilan bir xil ishlaydi. "
            "Eski frontend versiyalari uchun saqlangan — yangi kodda "
            "`/users/payment/link/<order_id>/` dan foydalaning."
        ),
        deprecated=True,
    ),
)
class PaymeLinkCreateApiView(PaymentLinkView):
    pass
