from rest_framework.generics import ListAPIView

from drf_spectacular.utils import extend_schema

from core.apps.shared.models import DocumentType
from core.apps.shared.serializers.document_type import DocumentTypeSerializer


@extend_schema(
    tags=['Document'],
    summary="Hujjat turlari ro'yxati",
    description=(
        "Mavjud hujjat turlarini (dissertatsiya, maqola va h.k.) qaytaradi. "
        "Hujjat yaratishda (`POST /shared/documents/`) va sertifikat yuklab "
        "olishda `type`/`document_type` maydoni uchun ID shu yerdan olinadi."
    ),
)
class DocumentTypeListAPIView(ListAPIView):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
