import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Eslatma matnlari (BE-04). Hozircha Telegram orqali; foydalanuvchining
# tg_id si bo'lmasa o'tkazib yuboriladi (SMS/email kanallari keyin qo'shiladi).
REMINDER_TEXTS = {
    '1h': (
        "⏰ Eslatma: №{order_id} buyurtmangiz uchun to'lov yakunlanmagan.\n"
        "To'lovni yakunlab, tekshiruv natijasini oching: {url}"
    ),
    '24h': (
        "📌 №{order_id} buyurtmangiz 24 soatdan beri to'lanmagan.\n"
        "Natija va sertifikatingiz sizni kutmoqda: {url}"
    ),
}


def _send_reminder(order, kind: str) -> None:
    from django.conf import settings
    from core.apps.shared.models.payment_reminder import PaymentReminder
    from core.apps.shared.utils.telegram import send_telegram_message

    # unique_together tufayli takror yaratish IntegrityError beradi —
    # get_or_create bilan idempotent qilamiz.
    reminder, created = PaymentReminder.objects.get_or_create(
        order=order, kind=kind,
    )
    if not created and reminder.delivered:
        return

    tg_id = order.user.tg_id if order.user else None
    if not tg_id:
        return

    doc_id = order.document_id or order.ai_document_id or ''
    url = f"{settings.FRONTEND_URL.rstrip('/')}/{doc_id}" if doc_id else settings.FRONTEND_URL
    text = REMINDER_TEXTS[kind].format(order_id=order.id, url=url)

    if send_telegram_message(tg_id, text):
        reminder.delivered = True
        reminder.save(update_fields=['delivered'])
        logger.info("To'lov eslatmasi yuborildi: order=%s kind=%s", order.id, kind)


@shared_task
def send_payment_reminders():
    """
    BE-04: to'lanmagan orderlar uchun 1 soat / 24 soat eslatmalari.
    Celery beat har 15 daqiqada chaqiradi.
    """
    from core.apps.shared.models import Order
    from core.apps.shared.serializers.payment_list import resolve_order_state

    now = timezone.now()
    windows = [
        # (tur, dan, gacha): yaratilganiga 1–24 soat bo'lgan orderlar '1h',
        # 24–72 soat bo'lganlar '24h' eslatma oladi.
        ('1h', now - timedelta(hours=24), now - timedelta(hours=1)),
        ('24h', now - timedelta(hours=72), now - timedelta(hours=24)),
    ]

    for kind, start, end in windows:
        orders = (
            Order.objects
            .select_related('user')
            .filter(created_at__gte=start, created_at__lt=end)
            .exclude(reminders__kind=kind, reminders__delivered=True)
        )
        for order in orders:
            try:
                if resolve_order_state(order) == 'paid':
                    continue
                _send_reminder(order, kind)
            except Exception:
                logger.exception(
                    "Eslatma yuborishda xato: order=%s kind=%s", order.id, kind
                )
