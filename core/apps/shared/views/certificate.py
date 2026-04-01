from django.shortcuts import render


CIRCUMFERENCE = 289.03

def certificate_view(request):
    return render(request, "sertifikat_1_2.html", {
        "certificate_number": "20260402 / 34007A1D",
        "created_date": "21.03.2026",
        "full_name": "Sokhibjon aaaOrzikulov",
        "file_name": "Resume / CV",
        "total_words": 1477,
        "unique_words": 593,
        "lexical_uniqueness": 40.15,
        "sentence_count": 105,
        "hash": "34007a1d41dd5d21ad8b450fc942a421",
        "originality": 90,
        "ai": 10,
        "plagiat": 0,
        "quote": 10,

        'originality_offset': round(CIRCUMFERENCE * (1 - 90 / 100), 2),
        'ai_offset':          50,
        'plagiat_offset':     round(CIRCUMFERENCE * (1 - 0 / 100), 2),
        'quote_offset':       round(CIRCUMFERENCE * (1 - 10 / 100), 2),
    })
