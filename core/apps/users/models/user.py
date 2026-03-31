from django.db import models
from django.contrib.auth.models import AbstractUser

from core.apps.users.manager.user import CustomUserManager
from core.apps.shared.models.base import BaseModel


class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True)
    username = None

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.phone)
