from django.db import models

from core.apps.shared.models import BaseModel


class DocumentType(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Hujjat turi'
        verbose_name_plural = 'Hujjat turlari'
