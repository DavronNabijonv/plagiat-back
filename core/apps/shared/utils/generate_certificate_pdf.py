"""
Sertifikat HTML → A4 Landscape PDF generator (Playwright)

Ishlatish:
    python3 generate_certificate_pdf.py

Chiqish:
    sertifikat.pdf  (Downloads papkasida)
"""

import math
import re
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# ── Ma'lumotlar (Django view'dan olingan) ──────────────────────────────────
DATA = {
    "certificate_number": "20260402 / 34007A1D",
    "created_date": "21.03.2026",
    "full_name": "Sokhibjon Orzikulov",
    "file_name": "Resume / CV",
    "total_words": 1477,
    "unique_words": 593,
    "lexical_uniqueness": "40.15",
    "sentence_count": 105,
    "hash": "34007a1d41dd5d21ad8b450fc942a421",
    "originality": 100,
    "ai": 100,
    "plagiat": 100,
    "quote": 100,
}

CIRCUMFERENCE = round(2 * math.pi * 46, 2)  # 289.03


def calc_offset(value_pct: float) -> float:
    """stroke-dashoffset = C * (1 - value/100)  →  full circle when value=100"""
    return round(CIRCUMFERENCE * (1 - value_pct / 100), 2)


def build_html(template_path: str) -> str:
    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    downloads_dir = Path(template_path).parent

    html = re.sub(r"\{%.*?%\}", "", html, flags=re.DOTALL)

    simple_vars = {
        "certificate_number": DATA["certificate_number"],
        "created_date": DATA["created_date"],
        "full_name": DATA["full_name"],
        "file_name": DATA["file_name"],
        "total_words": str(DATA["total_words"]),
        "unique_words": str(DATA["unique_words"]),
        "lexical_uniqueness": str(DATA["lexical_uniqueness"]),
        "sentence_count": str(DATA["sentence_count"]),
        "hash": DATA["hash"],
        "originality": str(DATA["originality"]),
        "ai": str(DATA["ai"]),
        "plagiat": str(DATA["plagiat"]),
        "quote": str(DATA["quote"]),
    }
    for key, val in simple_vars.items():
        html = re.sub(r"\{\{\s*" + key + r"\s*\}\}", val, html)

    CIRC = CIRCUMFERENCE

    orig_off = calc_offset(DATA["originality"])
    ai_off = calc_offset(DATA["ai"])
    plag_off = calc_offset(DATA["plagiat"])
    quot_off = calc_offset(DATA["quote"])

    offsets = [orig_off, ai_off, plag_off, quot_off]
    count = [0]

    def replace_offset(m):
        idx = count[0]
        count[0] += 1
        if idx < len(offsets):
            return f'stroke-dashoffset="{offsets[idx]}"'
        return m.group(0)

    html = re.sub(r'stroke-dashoffset="[\d.]+"', replace_offset, html)

    logo_candidates = [
        downloads_dir / "logo.png",
        downloads_dir / "anti-plagiat-logo.png",
    ]
    logo_src = ""
    for lc in logo_candidates:
        if lc.exists():
            logo_src = lc.as_uri()
            break

    if logo_src:
        html = re.sub(r'class="logo-img"\s+src=""', f'class="logo-img" src="{logo_src}"', html)
        html = re.sub(r'src=""\s+alt="Anti-Plagiat\.uz"', f'src="{logo_src}" alt="Anti-Plagiat.uz"', html)
    else:
        html = re.sub(
            r'<img\s+class="logo-img"[^>]*>',
            '<div style="color:#00c8e6;font-size:18px;font-weight:900;letter-spacing:2px;">ANTI-PLAGIAT.UZ</div>',
            html,
        )

    # Background rasm
    bg_img = downloads_dir / "5754469 (1).png"
    if bg_img.exists():
        html = html.replace("./5754469 (1).png", bg_img.as_uri())
    else:
        # Background rasm yo'q — olib tashlaymiz (bg-white overlay yetarli)
        html = re.sub(r'background-image:\s*url\([^)]*\);?', "", html)

    # ── 5. QR kod matnini yangilaymiz ────────────────────────────────────
    qr_text = (
        f"ANTI-PLAGIAT.UZ\\n"
        f"№ {DATA['certificate_number']}\\n"
        f"Shaxs: {DATA['full_name']}\\n"
        f"Originallik:{DATA['originality']}% | SI:{DATA['ai']}% | "
        f"Plagiat:{DATA['plagiat']}% | Iqtibos:{DATA['quote']}%\\n"
        f"MD5:{DATA['hash']}"
    )
    html = re.sub(
        r'text:\s*"[^"]*"',
        f'text: "{qr_text}"',
        html,
    )

    return html


def generate_pdf(html_content: str, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        page.set_content(html_content, wait_until="networkidle")

        # QR kod generatsiya bo'lishi uchun kutamiz
        page.wait_for_timeout(1500)

        # A4 Landscape: 297mm × 210mm
        page.pdf(
            path=output_path,
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )

        browser.close()
    print(f"✓ PDF yaratildi: {output_path}")