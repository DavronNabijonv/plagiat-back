from decimal import Decimal
from django.db import transaction

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from core.apps.shared.models import AiDocument, AiDocumentResult, Order
from core.apps.shared.utils.check_file import check_file, extract_text
from core.apps.shared.serializers.payment_list import resolve_order_state


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

    @extend_schema_field(
        serializers.ChoiceField(
            choices=['tolandi', 'kutilyabdi', 'tolanmagan'],
            help_text="Order to'lov holati",
        )
    )
    def get_state(self, obj):
        order = obj.orders.filter(type="ai_document").first()
        if not order:
            return 'tolanmagan'
        return resolve_order_state(order)

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_order_id(self, obj):
        order = obj.orders.filter(type="ai_document").first()
        return order.id if order else None
