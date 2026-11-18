from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


# Стандартный UserAdmin сортирует по логину; новых пользователей удобнее видеть первыми
admin.site.unregister(User)


@admin.register(User)
class SoloUserAdmin(UserAdmin):
    ordering = ("-date_joined",)
