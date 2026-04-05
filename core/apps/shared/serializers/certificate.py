from rest_framework import serializers


class CertificateDownloadSerializer(serializers.Serializer):
    full_name     = serializers.CharField(max_length=255)
    file_name     = serializers.CharField(max_length=255)
    document_type = serializers.CharField(max_length=255)
 
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
 
    def validate_document_type(self, value):
        return value.strip()
 
    def validate(self, attrs):
        document = self.context.get('document')
 
        if not document or not document.certificate_file:
            raise serializers.ValidationError(
                "Sertifikat hali tayyorlanmoqda, biroz kuting."
            )
        return attrs
