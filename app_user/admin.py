from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from app_user.models import CustomUser

class CustomUserAdmin(UserAdmin):
    """
    Кастомный класс для управления пользовательской моделью CustomUser в админке.
    """
    # Поля, которые будут отображаться в списке пользователей
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')

    # Поля, по которым можно выполнять поиск
    search_fields = ('username', 'email')

    # Поля, по которым можно фильтровать пользователей
    list_filter = ('is_staff', 'is_active', 'groups')

    # Настройка формы редактирования пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Настройка формы создания нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'is_staff', 'is_active'),
        }),
    )

    # Порядок сортировки пользователей
    ordering = ('-date_joined',)

# Регистрация модели CustomUser с кастомным классом админки
admin.site.register(CustomUser, CustomUserAdmin)