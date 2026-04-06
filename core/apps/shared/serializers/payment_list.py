from rest_framework import serializers

from core.apps.shared.models import Order, AiOrder


class UnifiedOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    turi = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    discount = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    state = serializers.SerializerMethodField()

    def get_turi(self, obj):
        if isinstance(obj, Order):
            return "Plagiat tekshiruvi"
        return "SI tekshiruvi"

    def get_discount(self, obj):
        if isinstance(obj, Order):
            BASE_PRICE = 41200
            discount = BASE_PRICE - float(obj.total_price)
            return max(discount, 0)
        return None 

    def get_state(self, obj):
        from payme.models import PaymeTransactions

        if isinstance(obj, Order):
            transaction = PaymeTransactions.objects.filter(account_id=obj.id).last()
        else:
            transaction = PaymeTransactions.objects.filter(account_id=obj.id).last()

        if transaction:
            return transaction.state
        return None
