from rest_framework import serializers

from core.apps.shared.models import Order
from core.apps.shared.serializers.document import DocumentSerializer

class OrderSerializer(serializers.ModelSerializer):
    document = DocumentSerializer()

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'document',
            'total_price'
        )

