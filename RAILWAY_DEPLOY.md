# Railway.app ga deploy qilish

Frontend (https://plagat.vercel.app) bilan test qilish uchun backend'ni
Railway'ga chiqarish yo'riqnomasi. Deploy `railway.json` +
`docker/Dockerfile.web` + `resources/scripts/entrypoint-railway.sh`
orqali avtomatik sozlangan.

## 1. Loyiha yaratish

1. https://railway.app → **New Project** → **Deploy from GitHub repo** →
   shu repo'ni tanlang (branch: `main` yoki `dev`).
2. Railway `railway.json` ni o'zi o'qiydi: Dockerfile bilan build qiladi,
   `entrypoint-railway.sh` (collectstatic + migrate + gunicorn) bilan ishga
   tushiradi.

## 2. PostgreSQL qo'shish

Project ichida **+ New** → **Database** → **PostgreSQL**.

## 3. Backend servisga environment variables

Backend servis → **Variables** → quyidagilarni qo'shing
(`${{Postgres.*}}` — Railway'ning reference variable sintaksisi,
Postgres servisidan avtomatik oladi):

```
SECRET_KEY=<kuchli-tasodifiy-qiymat>
DEBUG=True
ALLOWED_HOSTS=.up.railway.app,localhost

POSTGRES_DB=${{Postgres.PGDATABASE}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
POSTGRES_HOST=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}
# backup DB sifatida ham asosiy DB ko'rsatiladi (settings talab qiladi)
BACKUP_POSTGRES_DB=${{Postgres.PGDATABASE}}

CHAT_ID=<telegram chat id>
BOT_TOKEN=<telegram bot token>

PAYME_ID=<payme id>
PAYME_KEY=<payme key>

MULTICARD_APPLICATION_ID=<...>
MULTICARD_STORE_ID=<...>
MULTICARD_SECRET_KEY=<...>
MULTICARD_API_URL=https://dev-mesh.multicard.uz/api/v1
# Domen olingandan keyin shu qiymatni yangilang (5-qadam):
MULTICARD_CALLBACK_URL=https://<sizning-domen>.up.railway.app/payment/multicard/
```

Eslatma: test deploy uchun `DEBUG=True` qoldiring — static/media fayllar
Django'ning o'zi orqali xizmat qilinadi (alohida nginx yo'q).

## 4. Domen olish

Backend servis → **Settings** → **Networking** → **Generate Domain**.
Masalan: `plagiat-backend-production.up.railway.app`.

- `ALLOWED_HOSTS` dagi `.up.railway.app` wildcard bu domenni qamrab oladi.
- Admin panel CSRF'i uchun `https://*.up.railway.app`
  `CSRF_TRUSTED_ORIGINS` ga allaqachon qo'shilgan.
- Frontend (`https://plagat.vercel.app`) CORS ro'yxatida allaqachon bor.

## 5. Multicard callback'ni yangilash

Domen chiqqach `MULTICARD_CALLBACK_URL` ni real domen bilan yangilang:

```
MULTICARD_CALLBACK_URL=https://<domen>.up.railway.app/payment/multicard/
```

Endi Multicard webhooklari Railway'dagi backendga yetib keladi — lokaldagidek
simulyatsiya kerak emas, to'lov real sinaladi (sandbox API bilan).

## 6. (Ixtiyoriy) Celery worker — sertifikat PDF uchun

Sertifikat generatsiyasi Celery'da ishlaydi. Kerak bo'lsa:

1. **+ New** → **Database** → **Redis**.
2. **+ New** → **GitHub repo** → shu repo'ni yana qo'shing (ikkinchi servis).
3. Ikkinchi servisda **Settings → Deploy → Custom Start Command**:
   `celery -A config worker --loglevel=info`
4. Variables: backend servisdagi barcha o'zgaruvchilar + qo'shimcha:
   ```
   CELERY_BROKER_URL=${{Redis.REDIS_URL}}
   ```
5. Backend servisga ham `CELERY_BROKER_URL=${{Redis.REDIS_URL}}` qo'shing
   (tasklarni navbatga qo'yishi uchun).

Celery'siz ham API to'liq ishlaydi — faqat sertifikat PDF tayyorlanmaydi.

## 7. Tekshirish

Deploy tugagach:

- `https://<domen>.up.railway.app/api/docs/` — Swagger UI
- `https://<domen>.up.railway.app/admin/` — admin panel
  (superuser yaratish: servis **Settings → Deploy** emas, bir martalik:
  `railway run python manage.py createsuperuser` yoki Railway shell'da)

Frontend `.env` da API bazasini Railway domeniga qarating:
`https://<domen>.up.railway.app/api/v1/...`

## Muhim ogohlantirish — media fayllar

Railway konteyner fayl tizimi **efemerlik** — har redeploy'da yuklangan
fayllar (`resources/media/`: hujjatlar, sertifikatlar) o'chadi. Test uchun
bu yetarli. Saqlanishi kerak bo'lsa: servis **Settings → Volumes** →
**Add Volume**, mount path: `/code/resources/media`.
