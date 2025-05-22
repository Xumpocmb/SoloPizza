from decimal import Decimal
from django.db import models
from django.conf import settings
from app_catalog.models import Item, ItemParams, BoardParams, AddonParams, PizzaSauce


class CartQuerySet(models.QuerySet):
    def total_quantity(self):
        return sum(item.quantity for item in self)

    def total_sum(self):
        return sum(item.calculate_cart_total() for item in self)


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Товар')
    item_params = models.ForeignKey(ItemParams, on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    board = models.ForeignKey(BoardParams, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Борт')
    addons = models.ManyToManyField(AddonParams, blank=True, verbose_name='Добавки')
    sauce = models.ForeignKey(PizzaSauce, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Соус')

    objects = CartQuerySet.as_manager()
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'

    def __str__(self):
        return f'Корзина {self.user.username} | Продукт: {self.item.name} | {self.item_params.size.name}'

    def calculate_cart_total(self):
        """
        Рассчитывает полную стоимость товара в корзине, включая добавки и борт.
        """
        base_price = self.item_params.price * self.quantity
        addons_price = sum(addon.price for addon in self.addons.all())
        board_price = self.board.price if self.board else 0

        # Общая стоимость: базовая цена + борт + добавки, все умноженные на количество
        total_price = (base_price + board_price + addons_price) * self.quantity
        return total_price.quantize(Decimal(".01"))
