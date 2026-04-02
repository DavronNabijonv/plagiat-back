import math
import io
import re

import qrcode
import qrcode.image.svg
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render

# ── Doimiy qiymat ──────────────────────────────────────────────────────────
CIRCUMFERENCE = round(2 * math.pi * 34.5, 2)  # r=34.5 → 216.77


def _build_context(originality, ai, plagiat, quote):
    """Ikkala view ham ishlatiladigan umumiy context."""
    return {
        "certificate_number": "20260402 / 34007A1D",
        "created_date":        "21.03.2026",
        "full_name":           "Sokhibjon Orzikulov",
        "file_name":           "Resume / CV",
        "total_words":         1477,
        "unique_words":        593,
        "lexical_uniqueness":  40.15,
        "sentence_count":      105,
        "hash":                "34007a1d41dd5d21ad8b450fc942a421",
        "originality":         originality,
        "ai":                  ai,
        "plagiat":             plagiat,
        "quote":               quote,
        "circumference":       CIRCUMFERENCE,
        "originality_dash":    round(CIRCUMFERENCE * originality / 100, 2),
        "ai_dash":             round(CIRCUMFERENCE * ai          / 100, 2),
        "plagiat_dash":        round(CIRCUMFERENCE * plagiat     / 100, 2),
        "quote_dash":          round(CIRCUMFERENCE * quote       / 100, 2),
    }


def _make_qr_svg(context):
    """QR kodni inline SVG sifatida qaytaradi (weasyprint JS ishlatmaydi)."""
    text = (
        f"ANTI-PLAGIAT.UZ\n"
        f"No {context['certificate_number']}\n"
        f"Shaxs: {context['full_name']}\n"
        f"Originallik:{context['originality']}% | "
        f"SI:{context['ai']}% | "
        f"Plagiat:{context['plagiat']}% | "
        f"Iqtibos:{context['quote']}%\n"
        f"MD5:{context['hash']}"
    )
    factory = qrcode.image.svg.SvgPathImage
    img     = qrcode.make(text, image_factory=factory, box_size=3, border=1)
    buf     = io.BytesIO()
    img.save(buf)
    raw     = buf.getvalue().decode("utf-8")
    match   = re.search(r"<svg[\s\S]*</svg>", raw)
    return match.group(0) if match else ""


# ── HTML render view (brauzer uchun) ───────────────────────────────────────
def certificate_view(request):
    context = _build_context(
        originality=100,
        ai=100,
        plagiat=100,
        quote=100,
    )
    return render(request, "sertifikat_1_3.html", context)


# ── PDF yuklab olish view ──────────────────────────────────────────────────
def certificate_pdf_view(request):
    context = _build_context(
        originality=100,
        ai=100,
        plagiat=100,
        quote=100,
    )
    context["qr_svg"] = _make_qr_svg(context)

    html_string = render_to_string(
        "sertifikat_1_3.html",
        context,
        request,
    )
    pdf = HTML(
        string=html_string,
        base_url=request.build_absolute_uri(),
    ).write_pdf(
        stylesheets=[CSS(string="@page { size: A4 landscape; margin: 0; }")]
    )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sertifikat.pdf"'
    return response
