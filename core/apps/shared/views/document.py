from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions

from core.apps.shared.serializers.document import DocuemntCreateSerializer, DocumentSerializer
from core.apps.shared.models import Document, DocumentResult


class DocumentCreateView(GenericAPIView):
    serializer_class = DocuemntCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            document = serializer.save()
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class DocumentListApiView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            documents = Document.objects.filter(user=request.user)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
