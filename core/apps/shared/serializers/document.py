from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from core.apps.shared.models import Document, DocumentResult, Order, DocumentType
from core.apps.shared.utils.check_file import check_file
from payme.models import PaymeTransactions
from core.apps.shared.tasks.generate_certificate import generate_certificate_pdf


class DocuemntCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_null=False)
    file = serializers.FileField(allow_null=False)
    certificate = serializers.BooleanField(allow_null=False)
    text = serializers.CharField(required=False)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, write_only=True)
    type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.all())

    def create(self, validated_data):
        with transaction.atomic():
            base_price = Decimal('41200.00')
            file = validated_data.get('file')
            text = validated_data.get('text')
            request = self.context['request']
            type = validated_data.get('type')

            if validated_data.get("certificate"):
                base_price = Decimal('20600.00')

            now = timezone.now()
            orders_this_month = Order.objects.filter(
                user=request.user,
                created_at__year=now.year,
                created_at__month=now.month,
            ).values_list('id', flat=True)

            paid_count = PaymeTransactions.objects.filter(
                account_id__in=[str(oid) for oid in orders_this_month],
                state=PaymeTransactions.SUCCESSFULLY,
            ).count()

            if paid_count >= 10:
                total_price = base_price * Decimal('0.85')
            else:
                total_price = base_price

            document = Document.objects.create(
                title=validated_data['title'],
                file=file,
                certificate=validated_data['certificate'],
                text=text,
                user=request.user,
                type=type,
            )

            result, success = check_file(file=file, text=text)
            Order.objects.create(
                user=request.user,
                document=document,
                total_price=total_price,
                type="document"
            )

            if not success:
                raise serializers.ValidationError(f"Failed to check file: {result}")

            DocumentResult.objects.create(document=document, result_json=result)

            if document.certificate:
                generate_certificate_pdf.delay(
                    document_id = int(document.id),
                    base_url = str(request.build_absolute_uri('/')),
                )
            return document


class DocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentResult
        fields = ['id', 'document', 'result_json', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    results = DocumentResultSerializer(many=True, read_only=True)
    state = serializers.SerializerMethodField(read_only=True)
    order_id = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file',
            'certificate',
            'text',
            'created_at',
            'updated_at',
            'results',
            'state',
            "order_id",
            "certificate_file",
            "type",
        ]

    def get_type(self, obj):
        return {
            "id": obj.id,
            "name": obj.type.name,
        } if obj.type else None

    def get_state(self, obj):
        if not obj.orders.first():
            return 'unpaid'
        Payment = PaymeTransactions.objects.filter(account_id=obj.orders.first().id).first()
        if Payment:
            if Payment.state == 2:
                return 'paid'
        return 'unpaid'

    def get_order_id(self, obj):
        return obj.orders.first().id if obj.orders.first() else None
