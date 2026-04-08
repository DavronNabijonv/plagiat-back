from decimal import Decimal
from django.db import transaction

from rest_framework import serializers

from core.apps.shared.models import AiDocument, AiDocumentResult, Order
from core.apps.shared.utils.check_file import check_file, extract_text
from payme.models import PaymeTransactions


class AiDocuemntCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_null=False)
    file = serializers.FileField(allow_null=False)

    def create(self, validated_data):
        with transaction.atomic():
            file = validated_data.get('file')
            request = self.context['request']

            ai_document = AiDocument.objects.create(
                title=validated_data['title'],
                file=file,
                user=request.user,
            )
            result, success = check_file(file=file, text=None)
            txt_count = len(extract_text(file).split())
            total_price = txt_count * 5
            if total_price < 10000:
                total_price = Decimal(10000.00)
            ai_document.total_words = txt_count
            ai_document.save()

            order = Order.objects.create(
                user=request.user,
                ai_document=ai_document,
                total_price=total_price,
                type="ai_document",
            )

            if not success:
                raise serializers.ValidationError(f"Failed to check file: {result}")

            AiDocumentResult.objects.create(document=ai_document, result=result)

            return ai_document, order


class AiDocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiDocumentResult
        fields = ['id', 'document', 'result', 'created_at', 'updated_at']


class AiDocumentSerializer(serializers.ModelSerializer):
    result = AiDocumentResultSerializer(read_only=True)
    state = serializers.SerializerMethodField(read_only=True)
    order_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AiDocument
        fields = [
            'id',
            'title',
            'file',
            'created_at',
            'updated_at',
            'result',
            'state',
            "order_id",
            "total_words"
        ]

    def get_state(self, obj):
        order = obj.orders.filter(type="ai_document").first()
        if not order:
            return 'unpaid'
        Payment = PaymeTransactions.objects.filter(account_id=order.id).first()
        if Payment:
            if Payment.state == 2:
                return 'paid'
        return 'unpaid'

    def get_order_id(self, obj):
        order = obj.orders.filter(type="ai_document").first()
        return order.id if order else None
