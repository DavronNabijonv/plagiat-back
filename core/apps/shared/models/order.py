from django.db import models

from core.apps.shared.models import BaseModel

class Order(BaseModel):
    document = models.ForeignKey('shared.Document', on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders', null=True)
