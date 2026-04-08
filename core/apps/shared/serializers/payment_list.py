from rest_framework import serializers

from core.apps.shared.models import Order


class UnifiedOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    turi = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    discount = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    state = serializers.SerializerMethodField()

    def get_turi(self, obj):
        if obj.type == "document":
            return "Plagiat tekshiruvi"
        elif obj.type == "ai_document":
            return "SI tekshiruvi"
        else:
            return "Sertifikat"

    def get_discount(self, obj):
        if obj.type == "document":
            BASE_PRICE = 41200
            discount = BASE_PRICE - float(obj.total_price)
            return max(discount, 0)
        return None

    def get_state(self, obj):
        from payme.models import PaymeTransactions

        transaction = PaymeTransactions.objects.filter(account_id=obj.id).last()

        if transaction:
            return "paid" if transaction.state == 2 else "unpaid"
        return "unpaid"
