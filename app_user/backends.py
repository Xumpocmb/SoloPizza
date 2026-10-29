from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()


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
    Кастомный бэкенд аутентификации, использующий phone вместо username.
    """
    def authenticate(self, request, phone=None, password=None, **kwargs):
        if not phone or password is None:
            return None
        try:
            # Ищем пользователя по phone
            user = User.objects.filter(phone=phone).first()
            if user is None:
                return None
            # Проверяем пароль
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None