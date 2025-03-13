import re
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from app_user.validators import validate_phone_number_length


def clean_phone_number(phone_number):
    """
    Очищает номер телефона от всех символов, кроме цифр.
    """
    return re.sub(r'[^0-9]', '', phone_number)


class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=15, unique=True,
        validators=[
            validate_phone_number_length,
        ]
    )

    def save(self, *args, **kwargs):
        """
        Автоматически очищает номер телефона перед сохранением.
        """
        if self.phone_number:
            self.phone_number = clean_phone_number(self.phone_number)
        super().save(*args, **kwargs)
        if not self.username:
            self.username = str(uuid.uuid4())[:30]
        super().save(*args, **kwargs)