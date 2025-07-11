from django.apps import AppConfig


class AppCartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_cart'
    verbose_name = 'Корзины пользователей'

    # def ready(self):
    #     from django.contrib import admin
    #     from .models import CartItem
    #
    #     class CartItemAdmin(admin.ModelAdmin):
    #         list_select_related = ('user', 'item', 'item_variant', 'board', 'sauce')
    #
    #     admin.site.register(CartItem, CartItemAdmin)
