from rest_framework import serializers

from core.apps.shared.models.document_type import DocumentType


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'name']
