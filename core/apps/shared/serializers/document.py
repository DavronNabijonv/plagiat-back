from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field, inline_serializer

from core.apps.shared.models import Document, DocumentResult, Order, DocumentType
from core.apps.shared.utils.check_file import check_file
from core.apps.shared.utils.file_validation import validate_upload
from payme.models import PaymeTransactions
from core.apps.shared.serializers.payment_list import resolve_order_state
from core.apps.shared.tasks.generate_certificate import generate_certificate_pdf


# Narx komponentlari (frontend shared/lib/metadata.ts bilan mos)
SERVICE_FEE = Decimal('20600.00')
CERTIFICATE_PRICE = Decimal('20600.00')
AI_CHECK_PRICE = Decimal('10300.00')


class DocuemntCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_null=False)
    # BE-08: yagona fayl limiti (50MB) va format validatsiyasi
    file = serializers.FileField(allow_null=False, validators=[validate_upload])
    certificate = serializers.BooleanField(allow_null=False)
    # BE-07: AI-tekshiruvni qo'shimcha opsiya sifatida buyurtma qilish
    ai_check = serializers.BooleanField(required=False, default=False)
    text = serializers.CharField(required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.all())

    def create(self, validated_data):
        with transaction.atomic():
            file = validated_data.get('file')
            text = validated_data.get('text')
            request = self.context['request']
            type = validated_data.get('type')
            ai_check = validated_data.get('ai_check', False)

            base_price = SERVICE_FEE
            if validated_data.get("certificate"):
                base_price += CERTIFICATE_PRICE
            if ai_check:
                base_price += AI_CHECK_PRICE

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
                discount_price = base_price * Decimal('0.85')
            else:
                discount_price = base_price

            document = Document.objects.create(
                title=validated_data['title'],
                file=file,
                certificate=validated_data['certificate'],
                ai_check=ai_check,
                text=text,
                user=request.user,
                type=type,
            )

            result, success = check_file(file=file, text=text)
            order = Order.objects.create(
                user=request.user,
                document=document,
                total_price=discount_price,
                type="document"
            )

            if not success:
                raise serializers.ValidationError(f"Failed to check file: {result}")

            DocumentResult.objects.create(document=document, result_json=result)

            if document.certificate:
                generate_certificate_pdf.delay(
                    document_id=int(document.id),
                    base_url=str(request.build_absolute_uri('/')),
                )
            return document, order, discount_price


class DocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentResult
        fields = ['id', 'document', 'result_json', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    results = DocumentResultSerializer(many=True, read_only=True)
    state = serializers.SerializerMethodField(read_only=True)
    order_id = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)
    price_calculation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file',
            'certificate',
            'ai_check',
            'text',
            'created_at',
            'updated_at',
            'results',
            'state',
            "order_id",
            "certificate_file",
            "type",
            "price_calculation",
        ]

    @extend_schema_field(
        inline_serializer(
            name='DocumentTypeField',
            fields={
                'id': serializers.IntegerField(),
                'name': serializers.CharField(),
            },
        )
    )
    def get_type(self, obj):
        return {
            "id": obj.id,
            "name": obj.type.name,
        } if obj.type else None

    @extend_schema_field(
        serializers.ChoiceField(
            choices=['paid', 'unpaid'],
            help_text="Order to'lov holati",
        )
    )
    def get_state(self, obj):
        order = obj.orders.filter(type="document").first()
        if not order:
            return 'unpaid'
        return resolve_order_state(order)

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_order_id(self, obj):
        return obj.orders.filter(type="document").first().id if obj.orders.filter(type="document").first() else None

    @extend_schema_field(
        inline_serializer(
            name='PriceCalculationField',
            fields={
                'service_fee': serializers.FloatField(),
                'discount': serializers.FloatField(),
                'certificate': serializers.FloatField(),
                'total_price': serializers.FloatField(),
            },
        )
    )
    def get_price_calculation(self, obj):
        """Frontend to'lov oynasi uchun narx taqsimoti (BE-01/FE-01)."""
        order = obj.orders.filter(type="document").first()
        if not order:
            return None
        certificate = CERTIFICATE_PRICE if obj.certificate else Decimal('0.00')
        ai_check = AI_CHECK_PRICE if obj.ai_check else Decimal('0.00')
        base = SERVICE_FEE + certificate + ai_check
        discount = max(base - order.total_price, Decimal('0.00'))
        return {
            'service_fee': float(SERVICE_FEE),
            'discount': float(discount),
            'certificate': float(certificate),
            'total_price': float(order.total_price),
        }
