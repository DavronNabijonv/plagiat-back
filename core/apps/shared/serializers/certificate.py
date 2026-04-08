from rest_framework import serializers

from core.apps.shared.models import DocumentType


class CertificateDownloadSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    file_name = serializers.CharField(max_length=255)
    document_type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.all())

    def validate_full_name(self, value):
        value = value.strip()
        if len(value.split()) < 2:
            raise serializers.ValidationError("Ism va familiyani to'liq kiriting")
        return value

    def validate_file_name(self, value):
        value = value.strip()
        if any(ch in set('/\\:*?"<>|') for ch in value):
            raise serializers.ValidationError(
                'Fayl nomida /  \\ : * ? " < > | belgilar bo\'lishi mumkin emas'
            )
        return value

    def validate(self, attrs):
        document_type = attrs.get('document_type')
        document = self.context.get('document')

        type = DocumentType.objects.get(pk=document_type.id).name
        attrs['type'] = type
        if not document:
            raise serializers.ValidationError(
                "Hujjat mavjud emas."
            )
        if not document.certificate:
            raise serializers.ValidationError(
                "Sertifikat yuklab olish uchun to'lov qiling. 20600.00 so'm"
            )
        if not document.certificate_file:
            raise serializers.ValidationError(
                "Sertifikat tayyor emas, biroz kuting."
            )
        return attrs
