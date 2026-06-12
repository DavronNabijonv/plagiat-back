from django.db import models

from core.apps.shared.models.base import BaseModel


class CardRequisite(BaseModel):
    """
    BE-22/23: davlat → karta rekvizitlari → valyuta xaritasi.

    Har davlat foydalanuvchisi o'z valyutasida o'z kartasiga to'laydi
    (UZS — Uzcard/Humo, KZT — Kaspi, KGS — MBank va h.k.).
    Rekvizitlar va kurs admin tomonidan kiritiladi/yangilanadi.
    """
    country      = models.CharField(max_length=100, verbose_name="Davlat")
    country_code = models.CharField(
        max_length=2,
        verbose_name="Davlat kodi (ISO)",
        help_text="Masalan: UZ, KZ, KG, TJ",
    )
    currency     = models.CharField(
        max_length=3,
        verbose_name="Valyuta",
        help_text="Masalan: UZS, KZT, KGS, TJS",
    )
    card_number  = models.CharField(max_length=30, verbose_name="Karta raqami")
    card_holder  = models.CharField(max_length=200, verbose_name="Karta egasi")
    bank_name    = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Bank"
    )
    # 1 UZS necha birlik mahalliy valyutaga teng (UZS uchun 1.0).
    # Mahalliy summa = order narxi (UZS) * exchange_rate.
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, default=1,
        verbose_name="Kurs (1 UZS → mahalliy valyuta)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    def __str__(self):
        return f"{self.country} ({self.currency}) — {self.card_number}"

    class Meta:
        verbose_name = "Karta rekviziti"
        verbose_name_plural = "Karta rekvizitlari"


class CardTransferPayment(BaseModel):
    """
    BE-24/25: karta o'tkazmasi orqali to'lov (qo'lda tasdiqlash).

    Oqim: foydalanuvchi chek yuboradi → PENDING → admin tasdiqlaydi
    (APPROVED) → resolve_order_state 'paid' qaytaradi va natija ochiladi.
    Rad etilsa REJECTED — foydalanuvchi qayta urinishi mumkin.
    """
    PENDING  = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATE_CHOICES = [
        (PENDING,  'Tasdiq kutilmoqda'),
        (APPROVED, 'Tasdiqlandi'),
        (REJECTED, 'Rad etildi'),
    ]

    order = models.ForeignKey(
        'shared.Order',
        on_delete=models.CASCADE,
        related_name='card_transfers',
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='card_transfers',
    )
    requisite = models.ForeignKey(
        CardRequisite,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payments',
    )
    receipt = models.FileField(
        upload_to='card_receipts/',
        verbose_name="Chek (rasm/PDF)",
    )
    # Foydalanuvchi to'lagan summa — mahalliy valyutada
    amount   = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default='UZS')
    state    = models.CharField(
        max_length=10, choices=STATE_CHOICES, default=PENDING
    )

    # Audit jurnali (BE-25)
    admin_comment = models.TextField(null=True, blank=True, verbose_name="Izoh")
    reviewed_by   = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_card_transfers',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Chek #{self.id} — order {self.order_id} — {self.get_state_display()}"

    class Meta:
        verbose_name = "Karta o'tkazmasi (chek)"
        verbose_name_plural = "Karta o'tkazmalari (cheklar)"
        ordering = ['-created_at']
