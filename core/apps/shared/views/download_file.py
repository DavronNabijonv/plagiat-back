# views.py
import os
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.apps.shared.models import Document, AiDocument
from core.apps.shared.serializers.ai_document import AiDocuemntCreateSerializer


class OrderFileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            document = Document.objects.get(
                id=document_id,
                user=request.user
            )
        except Document.DoesNotExist:
            raise Http404("Document topilmadi")

        file_path = document.file.path

        if not os.path.exists(file_path):
            raise Http404("Fayl serverda topilmadi")

        file_name = os.path.basename(file_path)

        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=file_name
        )
        return response



class AiOrderFileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ai_document_id):
        try:
            ai_document = AiDocument.objects.get(
                id=ai_document_id,
                user=request.user
            )
        except AiDocument.DoesNotExist:
            raise Http404("AI Order topilmadi")

        file_path = ai_document.file.path

        if not os.path.exists(file_path):
            raise Http404("Fayl serverda topilmadi")

        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        return response
