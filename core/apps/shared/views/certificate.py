import math
import io
import re
import qrcode
import qrcode.image.svg
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime
from django.urls import reverse
from django.core.files.base import ContentFile
from pathlib import Path
import base64
from django.contrib.staticfiles import finders
import logging
import os


from core.apps.shared.models import Document, DocumentResult  # o'z app'ingizga qarab to'g'irlang
logger = logging.getLogger(__name__)

# ── Doimiy qiymat ─────────────────────────────────────────────────────────
CIRCUMFERENCE = round(2 * math.pi * 46, 2)  # r=46 → 289.03


def _get_logo_base64() -> str:
    from django.conf import settings
    logo_path = getattr(settings, 'LOGO_PATH', None)
    if not logo_path or not os.path.exists(logo_path):
        return ""
    with open(logo_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _build_context_from_result(document: Document, result: DocumentResult) -> dict:
    res       = result.result_json.get("res", {})
    analyze   = result.result_json.get("analyze_text", {})

    originality = res.get("originality", 0)
    ai          = res.get("ai", 0)
    plagiat     = res.get("plagiarism", 0)
    quote       = res.get("citation", 0)
    hash_val    = res.get("hash", "")

    total_words    = analyze.get("Общее количество слов", 0)
    unique_words   = analyze.get("Уникальных слов", 0)
    lexical_unique = analyze.get("Лексическая уникальность (%)", 0)
    sentence_count = analyze.get("Количество предложений", 0)

    cert_number = (
        f"{document.id:08d} / {hash_val[:8].upper()}"
        if hash_val else f"{document.id:08d}"
    )

    created_at = getattr(document, 'created_at', None)
    created_date = localtime(created_at).strftime("%d.%m.%Y") if created_at else "—"

    full_name = f"{document.user.first_name} {document.user.last_name}"

    return {
        "certificate_number": cert_number,
        "created_date":       created_date,
        "full_name":          full_name,
        "file_name":          document.title,
        "total_words":        total_words,
        "unique_words":       unique_words,
        "lexical_uniqueness": lexical_unique,
        "sentence_count":     sentence_count,
        "hash":               hash_val,
        "originality":        originality,
        "ai":                 ai,
        "plagiat":            plagiat,
        "quote":              quote,
        "circumference":      CIRCUMFERENCE,
        "originality_dash":   round(CIRCUMFERENCE * 100 / 100, 2),
        "ai_dash":            round(CIRCUMFERENCE * 100 / 100, 2),
        "plagiat_dash":       round(CIRCUMFERENCE * 100 / 100, 2),
        "quote_dash":         round(CIRCUMFERENCE * 100 / 100, 2),
        "logo_b64": _get_logo_base64(),
    }


def _make_qr_svg(url: str) -> str:
    factory = qrcode.image.svg.SvgPathImage
    img     = qrcode.make(url, image_factory=factory, box_size=3, border=1)
    buf     = io.BytesIO()
    img.save(buf)
    raw     = buf.getvalue().decode("utf-8")
    match   = re.search(r"<svg[\s\S]*</svg>", raw)
    return match.group(0) if match else ""


def _get_document_and_result(document_id: int):
    document = get_object_or_404(Document, id=document_id)
    result   = document.results.order_by('-id').first()
    if result is None:
        raise Http404("Bu hujjat uchun natija mavjud emas.")
    return document, result


def _generate_pdf(request, document: Document, result: DocumentResult) -> bytes:
    safe_title  = re.sub(r'[^\w\-]', '_', document.title)[:40]
    filename    = f"sertifikat_{safe_title}.pdf"
    css         = CSS(string="@page { size: A4 landscape; margin: 0; } body { margin: 0; padding: 0; }")

    context = _build_context_from_result(document, result)

    placeholder_url     = request.build_absolute_uri("/")
    context["qr_svg"]   = _make_qr_svg(placeholder_url)
    html_tmp            = render_to_string("sertifikat_pdf.html", context, request)
    pdf_tmp             = HTML(string=html_tmp, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[css])

    document.certificate_file.save(filename, ContentFile(pdf_tmp), save=True)

    cert_url          = request.build_absolute_uri(document.certificate_file.url)
    context["qr_svg"] = _make_qr_svg(cert_url)
    html_final        = render_to_string("sertifikat_pdf.html", context, request)
    pdf_final         = HTML(string=html_final, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[css])

    document.certificate_file.save(filename, ContentFile(pdf_final), save=True)

    return pdf_final


def certificate_view(request, document_id: int):
    """Browser ko'rinishi — HTML sertifikat."""
    document, result = _get_document_and_result(document_id)
    context = _build_context_from_result(document, result)

    if document.certificate_file:
        qr_url = request.build_absolute_uri(document.certificate_file.url)
    else:
        qr_url = request.build_absolute_uri(
            reverse('certificate_pdf', kwargs={'document_id': document_id})
        )

    context["qr_svg"] = _make_qr_svg(qr_url)
    return render(request, "sertifikat_pdf.html", context)


def certificate_pdf_view(request, document_id: int):
    document, result = _get_document_and_result(document_id)

    pdf_bytes = _generate_pdf(request, document, result)

    safe_title = re.sub(r'[^\w\-]', '_', document.title)[:40]
    filename   = f"sertifikat_{safe_title}.pdf"

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
