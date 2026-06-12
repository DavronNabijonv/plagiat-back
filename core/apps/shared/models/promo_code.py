from django.db import models
from django.utils import timezone

from core.apps.shared.models.base import BaseModel


class PromoCode(BaseModel):
    """
    BE-09: promo-kod va chegirma tizimi.
    Admin kod yaratadi; foydalanuvchi to'lov oynasida kiritadi —
    unpaid order narxiga foizli chegirma qo'llanadi.
    """
    code = models.CharField(max_length=40, unique=True, verbose_name="Kod")
    discount_percent = models.PositiveSmallIntegerField(
        verbose_name="Chegirma (%)",
        help_text="1–100 oralig'ida",
    )
    valid_until = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Amal qilish muddati",
        help_text="Bo'sh bo'lsa muddatsiz",
    )
    max_uses = models.PositiveIntegerField(
        default=0,
        verbose_name="Maksimal ishlatish",
        help_text="0 — cheksiz",
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name="Ishlatilgan")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.valid_until and self.valid_until < timezone.now():
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"

    class Meta:
        verbose_name = "Promo-kod"
        verbose_name_plural = "Promo-kodlar"


class PromoUsage(BaseModel):
    """Qaysi order qaysi kod bilan chegirma olgani — audit va takror oldini olish."""
    promo = models.ForeignKey(
        PromoCode, on_delete=models.CASCADE, related_name='usages'
    )
    order = models.OneToOneField(
        'shared.Order', on_delete=models.CASCADE, related_name='promo_usage'
    )
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='promo_usages'
    )
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.promo.code} → order {self.order_id}"

    class Meta:
        verbose_name = "Promo ishlatilishi"
        verbose_name_plural = "Promo ishlatilishlari"
