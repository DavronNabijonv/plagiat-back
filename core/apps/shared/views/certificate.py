import math
import io
import re
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import Http404, HttpResponse
from django.core.files.base import ContentFile
from django.utils.timezone import localtime
from pathlib import Path
import base64
import logging
import os

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.apps.shared.models import Document
from core.apps.shared.serializers.certificate import CertificateDownloadSerializer

logger        = logging.getLogger(__name__)
CIRCUMFERENCE = round(2 * math.pi * 46, 2)


def _get_logo_base64() -> str:
    from django.conf import settings
    logo_path = getattr(settings, 'LOGO_PATH', None)
    if not logo_path or not os.path.exists(logo_path):
        return ""
    with open(logo_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _make_qr_svg(url: str) -> str:
    import qrcode
    import qrcode.image.svg
    factory = qrcode.image.svg.SvgPathImage
    img     = qrcode.make(url, image_factory=factory, box_size=3, border=1)
    buf     = io.BytesIO()
    img.save(buf)
    raw   = buf.getvalue().decode("utf-8")
    match = re.search(r"<svg[\s\S]*</svg>", raw)
    return match.group(0) if match else ""


def _regenerate_pdf_with_overrides(
    request,
    document: Document,
    full_name: str,
    file_name: str,
    document_type: str,
) -> bytes:
    from core.apps.shared.models import DocumentResult

    result = document.results.order_by('-id').first()
    if result is None:
        raise ValueError("Natija topilmadi")

    res     = result.result_json.get("res", {})
    analyze = result.result_json.get("analyze_text", {})

    originality = res.get("originality", 0)
    plagiat     = res.get("plagiarism", 0)
    quote       = res.get("citation", 0)
    hash_val    = res.get("hash", "")

    cert_number  = f"{document.id:08d} / {hash_val[:8].upper()}" if hash_val else f"{document.id:08d}"
    created_at   = getattr(document, 'created_at', None)
    created_date = localtime(created_at).strftime("%d.%m.%Y") if created_at else "—"

    if document.certificate_file:
        qr_url = request.build_absolute_uri(document.certificate_file.url)
    else:
        qr_url = request.build_absolute_uri('/')

    context = {
        "certificate_number": cert_number,
        "created_date":       created_date,
        "full_name":          full_name,       # ← foydalanuvchi yozgani
        "TITLE":              document.title,
        "FILE":               file_name,       # ← foydalanuvchi yozgani
        "document_type":      document_type,   # ← foydalanuvchi yozgani
        "total_words":        analyze.get("Общее количество слов", 0),
        "unique_words":       analyze.get("Уникальных слов", 0),
        "lexical_uniqueness": analyze.get("Лексическая уникальность (%)", 0),
        "sentence_count":     analyze.get("Количество предложений", 0),
        "hash":               hash_val,
        "originality":        originality,
        "plagiat":            plagiat,
        "quote":              quote,
        "circumference":      CIRCUMFERENCE,
        "originality_dash":   round(CIRCUMFERENCE * originality / 100, 2),
        "plagiat_dash":       round(CIRCUMFERENCE * plagiat     / 100, 2),
        "quote_dash":         round(CIRCUMFERENCE * quote       / 100, 2),
        "logo_b64":           _get_logo_base64(),
        "qr_svg":             _make_qr_svg(qr_url),
    }

    css = CSS(string="@page { size: A4 landscape; margin: 0; } body { margin: 0; padding: 0; }")
    return HTML(
        string=render_to_string("sertifikat_pdf_9.html", context, request),
        base_url=request.build_absolute_uri('/'),
    ).write_pdf(stylesheets=[css], presentational_hints=True)



class CertificateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if document.certificate_file:
            return Response({"status": "ready"})
        return Response({"status": "processing"})


class CertificateDownloadView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CertificateDownloadSerializer

    def post(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CertificateDownloadSerializer(
            data=request.data,
            context={'request': request, 'document': document},
        )
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            pdf_bytes = _regenerate_pdf_with_overrides(
                request       = request,
                document      = document,
                full_name     = data['full_name'],
                file_name     = data['file_name'],
                document_type = data['document_type'],
            )
        except Exception:
            logger.exception("PDF render xatolik: document_id=%s", document_id)
            return Response(
                {"detail": "PDF tayyorlashda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        safe_title = re.sub(r'[^\w\-]', '_', document.title)[:40]
        filename   = f"sertifikat_{safe_title}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
