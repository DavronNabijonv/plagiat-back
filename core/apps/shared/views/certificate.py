# from django.shortcuts import render

# CIRCUMFERENCE = 289.03

# def certificate_view(request):
#     originality = 100
#     ai = 100
#     plagiat = 100
#     quote = 100

#     print(round(CIRCUMFERENCE * originality / 100, 2))

#     return render(request, "sertifikat_1_3.html", {
#         "certificate_number": "20260402 / 34007A1D",
#         "created_date": "21.03.2026",
#         "full_name": "Sokhibjon Orzikulov",
#         "file_name": "Resume / CV",
#         "total_words": 1477,
#         "unique_words": 593,
#         "lexical_uniqueness": 40.15,
#         "sentence_count": 105,
#         "hash": "34007a1d41dd5d21ad8b450fc942a421",
#         "originality": originality,
#         "ai": ai,
#         "plagiat": plagiat,
#         "quote": quote,
#         # Eski offset lar o'rniga:
#         "circumference": CIRCUMFERENCE,
#         "originality_dash": round(CIRCUMFERENCE * 100 / 100, 2),
#         "ai_dash":          round(CIRCUMFERENCE * 100 / 100, 2),
#         "plagiat_dash":     round(CIRCUMFERENCE * 100 / 100, 2),
#         "quote_dash":       round(CIRCUMFERENCE * 100 / 100, 2),
#     })

# def certificate_view(request):
#     originality = 100
#     ai = 100
#     plagiat = 100
#     quote = 100

#     print(round(CIRCUMFERENCE * originality / 100, 2))

#     return render(request, "sertifikat_1_3.html", {
#         "certificate_number": "20260402 / 34007A1D",
#         "created_date": "21.03.2026",
#         "full_name": "Sokhibjon Orzikulov",
#         "file_name": "Resume / CV",
#         "total_words": 1477,
#         "unique_words": 593,
#         "lexical_uniqueness": 40.15,
#         "sentence_count": 105,
#         "hash": "34007a1d41dd5d21ad8b450fc942a421",
#         "originality": originality,
#         "ai": ai,
#         "plagiat": plagiat,
#         "quote": quote,
#         # Eski offset lar o'rniga:
#         "circumference": CIRCUMFERENCE,
#         "originality_dash": round(CIRCUMFERENCE * 100 / 100, 2),
#         "ai_dash":          round(CIRCUMFERENCE * 100 / 100, 2),
#         "plagiat_dash":     round(CIRCUMFERENCE * 100 / 100, 2),
#         "quote_dash":       round(CIRCUMFERENCE * 100 / 100, 2),
#     })
    
# from weasyprint import HTML, CSS
# import qrcode, qrcode.image.svg, io, re

# def certificate_pdf_view(request):
#     # ... context ni tayyorlang (mavjud view kabi)
#     html_string = render_to_string("sertifikat_1_2.html", context, request)
#     pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(
#         stylesheets=[CSS(string="@page { size: A4 landscape; margin: 0; }")]
#     )
#     response = HttpResponse(pdf, content_type="application/pdf")
#     response["Content-Disposition"] = 'attachment; filename="sertifikat.pdf"'
#     return response