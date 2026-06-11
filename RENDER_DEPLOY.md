# Render.com ga deploy qilish

Frontend (https://plagat.vercel.app) bilan test qilish uchun backend'ni
Render'ga chiqarish yo'riqnomasi. Deploy `render.yaml` (Blueprint) +
`docker/Dockerfile.web` + `resources/scripts/entrypoint-render.sh`
orqali avtomatik sozlangan.

## 1. Blueprint orqali yaratish (tavsiya etiladi)

1. https://dashboard.render.com → **New** → **Blueprint**.
2. GitHub repo'ni ulang (branch: `main` yoki `dev`).
3. Render `render.yaml` ni o'qib ikkita resurs taklif qiladi:
   - `plagiat-db` — bepul PostgreSQL
   - `plagiat-backend` — Docker web servis
4. Shu sahifada `sync: false` deb belgilangan o'zgaruvchilar uchun qiymat
   so'raydi — lokal `.env` faylingizdan ko'chiring:
   ```
   CHAT_ID, BOT_TOKEN, PAYME_ID, PAYME_KEY,
   MULTICARD_APPLICATION_ID, MULTICARD_STORE_ID, MULTICARD_SECRET_KEY,
   MULTICARD_CALLBACK_URL (hozircha istalgan qiymat, 3-qadamda yangilanadi)
   ```
   `SECRET_KEY` so'ralmaydi — Render o'zi tasodifiy yaratadi.
   Postgres ulanish ma'lumotlari ham avtomatik bog'lanadi.
5. **Apply** bosing — build va deploy boshlanadi.

## 2. Domen

Render avtomatik domen beradi: `https://plagiat-backend.onrender.com`
(servis nomiga qarab). Hech narsa sozlash shart emas:

- `ALLOWED_HOSTS` dagi `.onrender.com` wildcard buni qamrab oladi.
- Admin panel CSRF'i uchun `https://*.onrender.com`
  `CSRF_TRUSTED_ORIGINS` da allaqachon bor.
- Frontend (`https://plagat.vercel.app`) CORS ro'yxatida allaqachon bor.

## 3. Multicard callback'ni yangilash

Servis ko'tarilgach **Environment** bo'limida:

```
MULTICARD_CALLBACK_URL=https://plagiat-backend.onrender.com/payment/multicard/
```

Endi Multicard webhooklari Render'dagi backendga yetib keladi — to'lov
sandbox API bilan real sinaladi, lokaldagidek simulyatsiya kerak emas.

## 4. Tekshirish

- `https://plagiat-backend.onrender.com/api/docs/` — Swagger UI
- `https://plagiat-backend.onrender.com/admin/` — admin panel

Superuser yaratish: servis sahifasida **Shell** tab (yoki SSH) →
```
python manage.py createsuperuser
```
(Eslatma: Shell/SSH bepul planda cheklangan bo'lishi mumkin — bo'lmasa
vaqtincha `python manage.py shell` ni lokalda Render DB'ga ulanib ishlating:
External Database URL ni `plagiat-db` sahifasidan olasiz.)

Frontend `.env` da API bazasini Render domeniga qarating:
`https://plagiat-backend.onrender.com/api/v1/...`

## 5. (Ixtiyoriy) Celery worker — sertifikat PDF uchun

Sertifikat generatsiyasi Celery'da ishlaydi. Kerak bo'lsa:

1. **New** → **Key Value** (Redis-mos, bepul plani bor) → yarating.
2. **New** → **Background Worker** → shu repo, runtime: Docker,
   Dockerfile: `docker/Dockerfile.web`,
   Start Command: `celery -A config worker --loglevel=info`.
   (Diqqat: Background Worker Render'da **pullik** planlarda ishlaydi.)
3. Worker'ga web servisdagi barcha env'lar + ikkalasiga ham:
   ```
   CELERY_BROKER_URL=<Key Value xizmatining Internal URL'i>
   ```

Celery'siz ham API to'liq ishlaydi — faqat sertifikat PDF tayyorlanmaydi.

## Bepul plan cheklovlari (bilib qo'ying)

- **Web servis uyquga ketadi**: 15 daqiqa trafik bo'lmasa to'xtaydi,
  keyingi so'rovda ~1 daqiqada uyg'onadi (birinchi so'rov sekin bo'ladi).
- **Bepul PostgreSQL muddati cheklangan** (~30 kun) — muddat tugashidan
  oldin Render ogohlantiradi; test ma'lumotlari uchun yetarli.
- **Disk efemerlik**: redeploy'da yuklangan fayllar (`resources/media/`:
  hujjatlar, sertifikatlar) o'chadi. Saqlash kerak bo'lsa servisga
  **Disk** ulang (pullik), mount path: `/code/resources/media`.

Bular faqat Render'dagi test muhitiga tegishli — production bazangizga
hech qanday aloqasi yo'q.
