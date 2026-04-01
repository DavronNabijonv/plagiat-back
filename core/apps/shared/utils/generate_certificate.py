
import io
import os
import struct
import math
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def _qr_make(data: str, box_size: int = 10, border: int = 2) -> Image.Image:
    try:
        import qrcode as _qr
        qr = _qr.QRCode(version=2, error_correction=_qr.constants.ERROR_CORRECT_M,
                         box_size=box_size, border=border)
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")
    except ImportError:
        pass

    size = 33  # 33x33 modules (QR v3 placeholder)
    cell = box_size
    img_size = (size + border * 2) * cell
    img = Image.new("RGB", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)

    def finder(r, c):
        for dr in range(7):
            for dc in range(7):
                x0 = (c + border + dc) * cell
                y0 = (r + border + dr) * cell
                x1 = x0 + cell
                y1 = y0 + cell
                outer = dr == 0 or dr == 6 or dc == 0 or dc == 6
                inner = 2 <= dr <= 4 and 2 <= dc <= 4
                color = "black" if (outer or inner) else "white"
                draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=color)

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for i in range(8, size - 8):
        color = "black" if i % 2 == 0 else "white"
        draw.rectangle([(i + border) * cell, (6 + border) * cell,
                         (i + border + 1) * cell - 1, (7 + border) * cell - 1], fill=color)
        draw.rectangle([(6 + border) * cell, (i + border) * cell,
                         (7 + border) * cell - 1, (i + border + 1) * cell - 1], fill=color)

    for i, ch in enumerate(data[:200]):
        r = 9 + (i // (size - 9))
        c = 9 + (i % (size - 9))
        if r < size and c < size:
            if ord(ch) % 2 == 0:
                draw.rectangle([(c + border) * cell, (r + border) * cell,
                                  (c + border + 1) * cell - 1, (r + border + 1) * cell - 1],
                                 fill="black")
    return img



def generate_certificate(
    output_path: str,
    first_name: str,
    last_name: str,
    background_image_path: str,
    logo_image_path: str = None,
    org_name_line1: str = "A.AVLONIY NOMIDAGI",
    org_name_line2: str = "PEDAGOGIK MAHORAT",
    org_name_line3: str = "MILLIY INSTITUTI",
    title_text: str = "SERTIFIKAT",
    file_label: str = "Tekshirilgan fayl nomi:",
    file_name: str = "",
    left_fields: dict = None,
    right_fields: dict = None,
    footer_text: str = "",
    qr_url: str = "https://example.com",
):
    """
    Sertifikat PDF yaratadi.

    Parametrlar:
        output_path          : PDF saqlanadigan joy
        first_name           : Ism
        last_name            : Familiya
        background_image_path: Background rasm yo'li (.png / .jpg)
        logo_image_path      : Logo rasm yo'li (ixtiyoriy)
        org_name_line1/2/3   : Tashkilot nomi (3 qator)
        title_text           : Sarlavha ("SERTIFIKAT")
        file_label           : "Tekshirilgan fayl nomi:" kabi label
        file_name            : Fayl yoki kurs nomi
        left_fields          : {"O'xshashlik:": "55.45%", "Originallik:": "44.55%"}
        right_fields         : {"Sertifikat raqami:": "ANT-...", "Berilgan vaqti:": "..."}
        footer_text          : Pastki manzil yoki matn
        qr_url               : QR code ichidagi URL (skanerlasa shu ochiladi)
    """

    page_w, page_h = landscape(A4)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    if background_image_path and os.path.exists(background_image_path):
        c.drawImage(background_image_path, 0, 0,
                    width=page_w, height=page_h,
                    preserveAspectRatio=False, mask='auto')

    logo_h = 55
    logo_w = 55
    org_x = page_w / 2
    top_y = page_h - 72

    if logo_image_path and os.path.exists(logo_image_path):
        total_w = logo_w + 8 + 160
        start_x = (page_w - total_w) / 2
        c.drawImage(logo_image_path, start_x, top_y - logo_h,
                    width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        text_x = start_x + logo_w + 10
    else:
        text_x = org_x - 80

    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.08, 0.25, 0.55)
    line_h = 13
    for i, line in enumerate([org_name_line1, org_name_line2, org_name_line3]):
        y = top_y - 14 - i * line_h
        c.drawString(text_x, y, line)

    c.setFont("Helvetica-Bold", 52)
    c.setFillColorRGB(0.12, 0.35, 0.65)
    title_w = c.stringWidth(title_text, "Helvetica-Bold", 52)
    c.drawString((page_w - title_w) / 2, page_h - 165, title_text)

    full_name = f"{first_name} {last_name}"
    c.setFont("Helvetica-Bold", 32)
    c.setFillColorRGB(0.05, 0.05, 0.05)
    name_w = c.stringWidth(full_name, "Helvetica-Bold", 32)
    name_y = page_h - 235
    c.drawString((page_w - name_w) / 2, name_y, full_name)

    line_margin = 80
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.8)
    c.line(line_margin, name_y - 8, page_w - line_margin, name_y - 8)

    c.setFont("Helvetica", 13)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    label_w = c.stringWidth(file_label, "Helvetica", 13)
    c.drawString((page_w - label_w) / 2, name_y - 38, file_label)

    if file_name:
        c.setFont("Helvetica-Bold", 13)
        c.setFillColorRGB(0.08, 0.08, 0.08)
        words = file_name.upper().split()
        lines = []
        current = ""
        for w in words:
            test = (current + " " + w).strip()
            if c.stringWidth(test, "Helvetica-Bold", 13) < page_w - 200:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)

        for i, ln in enumerate(lines):
            lw = c.stringWidth(ln, "Helvetica-Bold", 13)
            c.drawString((page_w - lw) / 2, name_y - 65 - i * 20, ln)

    # ── 7. CHAP MAYDONLAR ────────────────────────────────────────────────────
    if left_fields:
        lx = 100
        ly = name_y - 130
        for label, value in left_fields.items():
            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(lx, ly, label)
            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(0.08, 0.35, 0.65)
            c.drawString(lx + 130, ly, value)
            ly -= 24

    # ── 8. O'NG MAYDONLAR (QR chap tomoni) ───────────────────────────────────
    qr_size = 90
    qr_x = page_w - qr_size - 45
    qr_y = 38

    if right_fields:
        rx = page_w / 2 + 20
        ry = name_y - 130
        for label, value in right_fields.items():
            c.setFont("Helvetica-Bold", 11)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(rx, ry, label)
            c.setFont("Helvetica", 11)
            c.setFillColorRGB(0.15, 0.15, 0.15)
            c.drawString(rx, ry - 15, value)
            ry -= 42

    # ── 9. QR CODE ───────────────────────────────────────────────────────────
    qr_img = _qr_make(qr_url, box_size=8, border=1)
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=qr_size, height=qr_size)

    # ── 10. FOOTER ────────────────────────────────────────────────────────────
    if footer_text:
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        fw = c.stringWidth(footer_text, "Helvetica", 10)
        c.drawString((page_w - fw) / 2, 22, footer_text)

    c.save()
    return output_path


out = generate_certificate(
    output_path="/mnt/user-data/outputs/sertifikat_namuna.pdf",
    first_name="Nurullayeva",
    last_name="Aymira",
    background_image_path="/mnt/user-data/uploads/5754469__1_.png",
    logo_image_path=None,
    org_name_line1="A.AVLONIY NOMIDAGI",
    org_name_line2="PEDAGOGIK MAHORAT",
    org_name_line3="MILLIY INSTITUTI",
    title_text="SERTIFIKAT",
    file_label="Tekshirilgan fayl nomi:",
    file_name="BOSHLANG'ICH SINFLARDA MATEMATIK MASALALARNI YECHISH METODOLOGIYASI",
    left_fields={
        "O'xshashlik:": "55.45%",
        "Originallik:": "44.55%",
    },
    right_fields={
        "Sertifikat raqami:": "ANT-20260330-E2CC9450",
        "Berilgan vaqti:": "30.03.2026 06:57",
    },
    footer_text="antiplagiat.avloniy.uz",
    qr_url="https://antiplagiat.avloniy.uz/certificates/ANT-20260330-E2CC9450",
)




def download_cert(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id)
    
    output_path = os.path.join(settings.MEDIA_ROOT, 'certificates', f'{cert_id}.pdf')
    pdf_url = f"{settings.SITE_URL}/certificates/verify/{cert_id}/"

    generate_certificate(
        output_path=output_path,
        first_name=cert.first_name,
        last_name=cert.last_name,
        background_image_path=os.path.join(settings.BASE_DIR, 'static', 'certificates', 'background.png'),
        logo_image_path=os.path.join(settings.BASE_DIR, 'static', 'certificates', 'logo.png'),
        org_name_line1="SIZNING TASHKILOT",
        org_name_line2="NOMI",
        org_name_line3="",
        file_name=cert.course_name,
        left_fields={"O'xshashlik:": f"{cert.similarity}%", "Originallik:": f"{cert.originality}%"},
        right_fields={"Sertifikat raqami:": cert.cert_number, "Berilgan vaqti:": cert.issued_date.strftime("%d.%m.%Y %H:%M")},
        footer_text="yourdomain.uz",
        qr_url=pdf_url,
    )

    return FileResponse(open(output_path, 'rb'), content_type='application/pdf',
                        headers={'Content-Disposition': 'inline; filename="certificate.pdf"'})