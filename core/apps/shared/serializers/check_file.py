from rest_framework import serializers

from core.apps.shared.utils.file_validation import validate_upload


class CheckFileSerializer(serializers.Serializer):
    # BE-08: yagona fayl limiti (50MB) va format validatsiyasi
    file = serializers.FileField(validators=[validate_upload])
