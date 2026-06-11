import os
from django.http import FileResponse, Http404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.models import Document, AiDocument
from core.apps.shared.serializers.ai_document import AiDocuemntCreateSerializer


class DocumentFileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Document'],
        summary="Hujjatning asl faylini yuklab olish",
        description=(
            "Foydalanuvchi tekshiruvga yuborgan asl faylni qaytaradi "
            "(attachment sifatida). Frontend javobni blob qilib qabul qilishi "
            "kerak. Faqat o'z hujjatini yuklab olish mumkin."
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Fayl (attachment)"),
            404: OpenApiResponse(description="Hujjat yoki fayl topilmadi"),
        },
    )
    def get(self, request, id):
        try:
            document = Document.objects.get(
                id=id,
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

    @extend_schema(
        tags=['AI Document'],
        summary="AI hujjatning asl faylini yuklab olish",
        description=(
            "AI tekshiruvga yuborilgan asl faylni qaytaradi (attachment "
            "sifatida). Faqat o'z hujjatini yuklab olish mumkin."
        ),
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description="AI hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Fayl (attachment)"),
            404: OpenApiResponse(description="AI hujjat yoki fayl topilmadi"),
        },
    )
    def get(self, request, id):
        try:
            ai_document = AiDocument.objects.get(
                id=id,
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
