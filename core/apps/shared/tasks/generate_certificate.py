import math
import io
import re
import qrcode
import qrcode.image.svg
from celery import shared_task
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils.timezone import localtime
from pathlib import Path
import base64
import logging
import os

from core.apps.shared.models import Document

logger      = logging.getLogger(__name__)
CIRCUMFERENCE = round(2 * math.pi * 46, 2)


def _get_logo_base64() -> str:
    from django.conf import settings
    logo_path = getattr(settings, 'LOGO_PATH', None)
    if not logo_path or not os.path.exists(logo_path):
        return ""
    with open(logo_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _make_qr_svg(url: str) -> str:
    factory = qrcode.image.svg.SvgPathImage
    img     = qrcode.make(url, image_factory=factory, box_size=3, border=1)
    buf     = io.BytesIO()
    img.save(buf)
    raw   = buf.getvalue().decode("utf-8")
    match = re.search(r"<svg[\s\S]*</svg>", raw)
    return match.group(0) if match else ""


def _build_context(document: Document, result) -> dict:
    res     = result.result_json.get("res", {})
    analyze = result.result_json.get("analyze_text", {})

    originality = res.get("originality", 0)
    plagiat     = res.get("plagiarism", 0)
    quote       = res.get("citation", 0)
    hash_val    = res.get("hash", "")

    cert_number  = f"{document.id:08d} / {hash_val[:8].upper()}" if hash_val else f"{document.id:08d}"
    created_at   = getattr(document, 'created_at', None)
    created_date = localtime(created_at).strftime("%d.%m.%Y") if created_at else "—"
    full_name    = f"{document.user.first_name} {document.user.last_name}".strip() or document.user.username

    return {
        "certificate_number": cert_number,
        "created_date":       created_date,
        "full_name":          full_name,
        "TITLE":              document.title,
        "FILE":               Path(document.file.name).name,
        "document_type":      getattr(document, 'document_type', ''),
        "total_words":        analyze.get("Общее количество слов", 0),
        "unique_words":       analyze.get("Уникальных слов", 0),
        "lexical_uniqueness": analyze.get("Лексическая уникальность (%)", 0),
        "sentence_count":     analyze.get("Количество предложений", 0),
        "hash":               hash_val,
        "originality":        originality,
        "plagiat":            plagiat,
        "quote":              quote,
        "circumference":      CIRCUMFERENCE,
        "originality_dash":   100,
        "plagiat_dash":       100,
        "quote_dash":         100,
        "logo_b64":           _get_logo_base64(),
        "qr_svg":             "",
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_certificate_pdf(self, document_id: int, base_url: str):
    """
    DocumentCreateSerializer.create() dan chaqiriladi.
    certificate=True bo'lsa PDF yaratib certificate_file ga saqlaydi.
    """
    try:
        document = Document.objects.select_related('user').get(id=document_id)
        result   = document.results.order_by('-id').first()

        if result is None:
            raise self.retry(countdown=5)

        context    = _build_context(document, result)
        css        = CSS(string="@page { size: A4 landscape; margin: 0; } body { margin: 0; padding: 0; }")
        safe_title = re.sub(r'[^\w\-]', '_', document.title)[:40]
        filename   = f"sertifikat_{safe_title}.pdf"

        context["qr_svg"] = _make_qr_svg(base_url)
        pdf_tmp = HTML(
            string=render_to_string("sertifikat_pdf_9.html", context),
            base_url=base_url,
        ).write_pdf(stylesheets=[css], presentational_hints=True)
        document.certificate_file.save(filename, ContentFile(pdf_tmp), save=True)

        cert_url          = base_url.rstrip('/') + document.certificate_file.url
        context["qr_svg"] = _make_qr_svg(cert_url)
        pdf_final = HTML(
            string=render_to_string("sertifikat_pdf_9.html", context),
            base_url=base_url,
        ).write_pdf(stylesheets=[css], presentational_hints=True)
        document.certificate_file.save(filename, ContentFile(pdf_final), save=True)

        logger.info("Certificate PDF tayyor: document_id=%s", document_id)

    except Document.DoesNotExist:
        logger.error("Document topilmadi: id=%s", document_id)
    except Exception as exc:
        logger.exception("Certificate PDF xatolik: document_id=%s", document_id)
        raise self.retry(exc=exc)
