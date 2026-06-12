import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, text: str) -> bool:
    """
    BOT_TOKEN orqali foydalanuvchiga (tg_id) xabar yuboradi.
    BE-04 eslatmalari va BE-25 tasdiqlash xabarlari shu yerdan o'tadi.
    Xato bo'lsa log yozadi, exception tashlamaydi (notification best-effort).
    """
    token = getattr(settings, 'BOT_TOKEN', None)
    if not token or not chat_id:
        return False

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(
                "Telegram xabar yuborilmadi: chat_id=%s status=%s body=%s",
                chat_id, resp.status_code, resp.text[:200],
            )
            return False
        return True
    except requests.RequestException:
        logger.exception("Telegram so'rovi xato: chat_id=%s", chat_id)
        return False
