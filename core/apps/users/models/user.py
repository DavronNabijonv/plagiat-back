from django.db import models
from django.contrib.auth.models import AbstractUser

from core.apps.users.manager.user import CustomUserManager
from core.apps.shared.models.base import BaseModel


class User(AbstractUser):
    tg_id    = models.CharField(max_length=200, null=True, blank=True)
    phone    = models.CharField(max_length=20, unique=True)
    username = None
    # Shaxsiy balans — so'mda. To'lov tasdiqlanganida oshiriladi,
    # xizmat uchun to'langanda kamaytiriladi.
    balance  = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.phone)
