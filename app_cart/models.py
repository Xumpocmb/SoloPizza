from django.db import models
from django.conf import settings
from app_catalog.models import Item, ItemParams, BoardParams, AddonParams

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Товар')
    item_params = models.ForeignKey(ItemParams, on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    board = models.ForeignKey(BoardParams, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Борт')
    addons = models.ManyToManyField(AddonParams, blank=True, verbose_name='Добавки')

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'

    def __str__(self):
        return f'Корзина {self.user.username} | Продукт: {self.item.name} | {self.item_params.size.name}'