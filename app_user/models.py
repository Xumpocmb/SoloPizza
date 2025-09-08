from django.db import models
from django.contrib.auth.models import User

# Расширение модели пользователя
User.add_to_class('phone', models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон'))
# Добавляем поле для хранения адреса пользователя
User.add_to_class('address', models.TextField(blank=True, null=True, verbose_name='Адрес'))
