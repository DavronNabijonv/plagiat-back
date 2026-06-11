from django.db import models
from core.apps.shared.models.base import BaseModel


class BalanceTopup(BaseModel):
    """
    Foydalanuvchi balansi to'ldirish so'rovi.

    Nima uchun alohida model:
    - To'lov tasdiqlangandan keyingina (MulticardTransaction.state=PAID)
      user.balance oshiriladi.
    - Tarix saqlanadi: qachon, qancha to'ldirilgan.
    - is_applied=True bo'lsa balans allaqachon qo'shilgan,
      webhook ikkinchi marta kelsa ikki marta qo'shib yubormaymiz (idempotent).
    """
    user       = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='topups',
    )
    amount     = models.DecimalField(max_digits=15, decimal_places=2)
    is_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} — +{self.amount} so'm"
