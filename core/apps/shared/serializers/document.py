from django.db import transaction

from rest_framework import serializers

from core.apps.shared.models import Document, DocumentResult, Order
from core.apps.shared.utils.check_file import check_file


class DocuemntCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    file = serializers.FileField()
    certificate = serializers.BooleanField()
    text = serializers.CharField(required=False)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, write_only=True)

    def create(self, validated_data):
        with transaction.atomic():
            total_price = validated_data.pop('total_price')  # 🔥 muhim
            file = validated_data.get('file')
            text = validated_data.get('text')
            document = Document.objects.create(
                title=validated_data['title'],
                file=file,
                certificate=validated_data['certificate'],
                text=validated_data.get('text'),
                user=self.context['request'].user
            )
            result, success = check_file(file=file, text=text)
            Order.objects.create(user=self.context['request'].user, document=document, total_price=total_price)
            if success:
                DocumentResult.objects.create(document=document, result_json=result)
                return document
            else:
                raise serializers.ValidationError("Failed to check file")


class DocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentResult
        fields = ['id', 'document', 'result_json', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    results = DocumentResultSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'certificate', 'text', 'created_at', 'updated_at', 'results']
