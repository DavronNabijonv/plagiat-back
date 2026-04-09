import os
import subprocess
from datetime import datetime

import requests
from django.conf import settings


def create_and_send_backup(
    db_host,
    db_user,
    db_name,
    db_password,
    chat_id,
    bot_token
):
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.sql"
    filepath = os.path.join(settings.BASE_DIR, "resources/backups", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    command = [
        "pg_dump",
        "-h",
        db_host,
        "-U",
        db_user,
        db_name,
    ]

    enviroment = os.environ.copy()
    enviroment["PGPASSWORD"] = db_password

    with open(filepath, "w") as f:
        subprocess.run(command, stdout=f, env=enviroment)

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M")
    with open(filepath, "rb") as file:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": f"📦 *#anti_plagiat*\n📅 {date} {time}\n✅ Backup tayyor",
                "parse_mode": "Markdown",
            },
            files={"document": file},
        )

    return f"Backup sent: {filename}"
