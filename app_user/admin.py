from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


# Стандартный UserAdmin сортирует по логину; новых пользователей удобнее видеть первыми
admin.site.unregister(User)


@admin.register(User)
class SoloUserAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = (*UserAdmin.list_display, "sign_in")
    list_filter = (*UserAdmin.list_filter, ("socialaccount__provider", admin.AllValuesFieldListFilter))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("socialaccount_set")

    @admin.display(description="Вход через")
    def sign_in(self, user):
        # пусто — регистрация на сайте по email; Apple бывает только из приложения
        return ", ".join(sorted(account.provider.capitalize() for account in user.socialaccount_set.all()))
