from django.db import models

from core.apps.shared.models import BaseModel

class AiOrder(BaseModel):
    ai_document = models.OneToOneField('shared.AiDocument', on_delete=models.CASCADE, related_name='ai_order')
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='ai_orders', null=True)

    def __str__(self):
        return f"{self.id} - {self.total_price}"

    class Meta:
        verbose_name = 'SI Buyurtma'
        verbose_name_plural = 'SI Buyurtmalar'
