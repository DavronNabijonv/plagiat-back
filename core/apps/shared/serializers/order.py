from rest_framework import serializers

from core.apps.shared.models import Order, AiOrder
from core.apps.shared.serializers.document import DocumentSerializer
from core.apps.shared.serializers.ai_document import AiDocumentSerializer

class OrderSerializer(serializers.ModelSerializer):
    document = DocumentSerializer()

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'document',
            'total_price',
        )



class AiOrderSerializer(serializers.ModelSerializer):
    ai_document = AiDocumentSerializer()

    class Meta:
        model = AiOrder
        fields = (
            'id',
            'user',
            'ai_document',
            'total_price',
        )

