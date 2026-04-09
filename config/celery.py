import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config", broker="redis://redis:6379", backend="redis://redis:6379")


app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "daily-postgres-backup": {
        "task": "core.apps.shared.tasks.backup.postgres_backup",
        "schedule": crontab(hour=0, minute=0),
        # "schedule": crontab(minute="*/1"),
    },
}
