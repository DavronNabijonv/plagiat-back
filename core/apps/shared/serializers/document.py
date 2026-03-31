from django.db import transaction

from rest_framework import serializers

from core.apps.shared.models import Document, DocumentResult
from core.apps.shared.utils.check_file import check_file


class DocuemntCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['title', 'file', 'certificate', 'text']

    def create(self, validated_data):
        with transaction.atomic():
            file = validated_data.get('file')
            document = Document.objects.create(
                title=validated_data['title'],
                file=file,
                certificate=validated_data['certificate'],
                text=validated_data.get('text'),
                user=self.context['request'].user
            )
            result, success = check_file(file)
            DocumentResult.objects.create(document=document, result_json=result)
            return document


class DocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentResult
        fields = ['id', 'document', 'result_json', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    results = DocumentResultSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'certificate', 'text', 'created_at', 'updated_at', 'results']
