import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Docker compose'da redis servisi, Railway'da esa Redis plugin URL'i ishlatiladi
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", BROKER_URL)

app = Celery("config", broker=BROKER_URL, backend=RESULT_BACKEND)


app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "daily-postgres-backup": {
        "task": "core.apps.shared.tasks.backup.postgres_backup",
        "schedule": crontab(hour=0, minute=0),
        # "schedule": crontab(minute="*/1"),
    },
    # BE-04: to'lanmagan orderlar uchun 1 soat / 24 soat eslatmalari
    "unpaid-payment-reminders": {
        "task": "core.apps.shared.tasks.payment_reminder.send_payment_reminders",
        "schedule": crontab(minute="*/15"),
    },
}
