from django.db import models

from core.apps.shared.models import BaseModel

class Order(BaseModel):
    document = models.ForeignKey('shared.Document', on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
    ai_document = models.ForeignKey('shared.AiDocument', on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)

    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders', null=True)

    type = models.CharField(max_length=100, choices=[('certificate', 'Certificate'), ('document', 'Document'), ('ai_document', 'AI Document')], default='document')

    payment_provider = models.CharField(
        max_length=20,
        choices=[
            ('multicard', 'Multicard'),
            ('balance', 'Balans'),
            ('payme', 'Payme'),
            # BE-22: karta o'tkazmasi (qo'lda tasdiqlash)
            ('card_transfer', "Karta o'tkazmasi"),
        ],
        null=True, blank=True,
    )

    def __str__(self):
        return f"{self.id} - {self.type} - {self.total_price}"

    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
