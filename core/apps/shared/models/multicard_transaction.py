from django.db import models
from core.apps.shared.models.base import BaseModel


class MulticardTransaction(BaseModel):
    """
    Multicard tomonidan qaytarilgan har bir to'lov sessiyasi.

    order  — oddiy xizmat to'lovi (document/ai_document/certificate).
             Agar balans to'ldirish bo'lsa None bo'ladi.
    topup  — balans to'ldirish to'lovi.
             Agar xizmat to'lovi bo'lsa None bo'ladi.
    """
    CREATED   = 1
    PAID      = 2
    CANCELLED = -1

    STATE_CHOICES = [
        (CREATED,   'Yaratildi'),
        (PAID,      'To\'landi'),
        (CANCELLED, 'Bekor qilindi'),
    ]

    # Multicard tomonidan beriladigan unikal sessiya IDsi
    transaction_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    # Xizmat to'lovi uchun
    order = models.ForeignKey(
        'shared.Order',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='multicard_transactions',
    )
    # Balans to'ldirish uchun
    topup = models.ForeignKey(
        'shared.BalanceTopup',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='multicard_transactions',
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    state  = models.IntegerField(choices=STATE_CHOICES, default=CREATED)

    def __str__(self):
        return f"Multicard #{self.transaction_id} — {self.amount}"
