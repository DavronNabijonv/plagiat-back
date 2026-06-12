from django.db import models

from core.apps.shared.models.base import BaseModel


class PaymentReminder(BaseModel):
    """
    BE-04: to'lanmagan order uchun yuborilgan eslatmalar jurnali.
    Har order uchun har tur ('1h' / '24h') eslatma faqat bir marta yuboriladi.
    """
    KIND_1H = '1h'
    KIND_24H = '24h'

    KIND_CHOICES = [
        (KIND_1H, '1 soatdan keyin'),
        (KIND_24H, '24 soatdan keyin'),
    ]

    order = models.ForeignKey(
        'shared.Order',
        on_delete=models.CASCADE,
        related_name='reminders',
    )
    kind = models.CharField(max_length=4, choices=KIND_CHOICES)
    # Qaysi kanal orqali yetkazildi (hozircha telegram; SMS/email keyin)
    channel = models.CharField(max_length=20, default='telegram')
    delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.order_id} — {self.kind} eslatma"

    class Meta:
        verbose_name = "To'lov eslatmasi"
        verbose_name_plural = "To'lov eslatmalari"
        unique_together = [('order', 'kind')]
