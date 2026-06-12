CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    # Test backend serveri
    "http://82.25.190.233:8001",
    "https://plagat.vercel.app",
    "https://anti-plagiat.uz",
    "https://dev.anti-plagiat.uz",
    "https://plagat-ei6yousn1-davronnabijonvs-projects.vercel.app",
    # Dev branch deploy — frontni testlash uchun (prod emas)
    "https://plagat-git-dev-davronnabijonvs-projects.vercel.app",
]

# Vercel'ning preview deploylari (har push'da yangi subdomain) uchun
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://plagat-[\w-]+-davronnabijonvs-projects\.vercel\.app$",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    # Test backend serveri (admin panelga kirish uchun)
    "http://82.25.190.233:8001",
    "https://plaget.felixits.uz",
    "https://plagat.vercel.app",
    "https://api.anti-plagiat.uz",
    "https://anti-plagiat.uz",
    "https://dev-api.anti-plagiat.uz",
    "https://dev.anti-plagiat.uz",
    "https://plagat-ei6yousn1-davronnabijonvs-projects.vercel.app",
    # Dev branch deploy — frontni testlash uchun (prod emas)
    "https://plagat-git-dev-davronnabijonvs-projects.vercel.app",
    # Render test deploy (admin panelga kirish uchun)
    "https://*.onrender.com",
]
