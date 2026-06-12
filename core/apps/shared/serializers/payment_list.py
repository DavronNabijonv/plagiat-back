from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from payme.models import PaymeTransactions
from core.apps.shared.models.multicard_transaction import MulticardTransaction
from core.apps.shared.models import Order


def resolve_order_state(order) -> str:
    """
    Order obyektining to'lov holatini qaytaradi: 'paid' yoki 'unpaid'.
    Yagona joy — qo'shilgan har bir provider shu yerda yangilanadi.
    Frontend faqat shu ikki qiymatni biladi; invoice yaratilgan-u
    to'lanmagan holat ham 'unpaid' (foydalanuvchi qayta to'lay oladi).
    """
    provider = order.payment_provider

    if provider == 'balance':
        return 'paid'

    if provider == 'multicard':
        tx = MulticardTransaction.objects.filter(order=order).last()
        if tx and tx.state == MulticardTransaction.PAID:
            return 'paid'
        return 'unpaid'

    # payme yoki None (eski orderlar)
    tx = PaymeTransactions.objects.filter(account_id=order.id).last()
    if tx and tx.state == 2:
        return 'paid'
    return 'unpaid'


class UnifiedOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    turi = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    discount = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    state = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.ChoiceField(
            choices=['Plagiat tekshiruvi', 'SI tekshiruvi', 'Sertifikat'],
            help_text="Order turi (ko'rsatish uchun tayyor matn)",
        )
    )
    def get_turi(self, obj):
        if obj.type == "document":
            return "Plagiat tekshiruvi"
        elif obj.type == "ai_document":
            return "SI tekshiruvi"
        else:
            return "Sertifikat"

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_discount(self, obj):
        if obj.type == "document":
            BASE_PRICE = 41200
            discount = BASE_PRICE - float(obj.total_price)
            return max(discount, 0)
        return None

    @extend_schema_field(
        serializers.ChoiceField(
            choices=['paid', 'unpaid'],
            help_text="To'lov holati",
        )
    )
    def get_state(self, obj):
        return resolve_order_state(obj)
