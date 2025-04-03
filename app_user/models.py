import re
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from app_user.validators import validate_phone_number_length


def clean_phone_number(phone_number):
    """
    Очищает номер телефона от всех символов, кроме цифр.
    """
    return re.sub(r'[^0-9]', '', phone_number)


class CustomUser(AbstractUser):
    username = models.CharField(
        verbose_name='Номер телефона',
        unique=True,
        max_length=20,
        validators=[validate_phone_number_length],
    )

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def clean_phone_number(self):
        """
        Очищает номер телефона от всех символов, кроме цифр.
        """
        return re.sub(r'[^0-9]', '', self.username)

    def save(self, *args, **kwargs):
        # Очищаем номер телефона перед сохранением
        self.username = self.clean_phone_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Телефон: {self.username}'