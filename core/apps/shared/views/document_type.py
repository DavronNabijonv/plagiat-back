from rest_framework.generics import ListAPIView

from core.apps.shared.models import DocumentType
from core.apps.shared.serializers.document_type import DocumentTypeSerializer



class DocumentTypeListAPIView(ListAPIView):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
