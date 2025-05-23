from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
from django.contrib.auth.backends import BaseBackend


# class PhoneNumberBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             # Попробуем найти пользователя по номеру телефона
#             user = CustomUser.objects.get(phone_number=username)
#             # Проверяем пароль
#             if user.check_password(password):
#                 return user
#         except CustomUser.DoesNotExist:
#             return None
#
#     def get_user(self, user_id):
#         try:
#             return CustomUser.objects.get(pk=user_id)
#         except CustomUser.DoesNotExist:
#             return None



class PhoneNumberAuthBackend(BaseBackend):
    """
    Кастомный бэкенд аутентификации, использующий phone_number вместо username.
    """
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            # Ищем пользователя по phone_number
            user = CustomUser.objects.get(phone_number=phone_number)
            # Проверяем пароль
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None