import os
import subprocess
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings

from config.env import env
from core.services.backup import create_and_send_backup


@shared_task
def postgres_backup():
    create_and_send_backup(
        db_host=env.str("POSTGRES_HOST"),
        db_user=env.str("POSTGRES_USER"),
        db_name=env.str("POSTGRES_DB"),
        db_password=env.str("POSTGRES_PASSWORD"),
        chat_id=settings.CHAT_ID,
        bot_token=settings.BOT_TOKEN,
    )
    