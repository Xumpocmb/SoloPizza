from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce


class CartQuerySet(models.QuerySet):
    def total_quantity(self):
        return sum(item.quantity for item in self)

    def total_sum(self):
        return sum(item.calculate_cart_total() for item in self)


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    item = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    item_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        verbose_name='Вариант товара',
        help_text='Выбранный размер/вариант товара',
        null=True,
        blank=True
    ) #TODO: remove null and blank
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    board = models.ForeignKey(
        BoardParams,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Борт',
        help_text='Только для пиццы'
    )
    addons = models.ManyToManyField(
        AddonParams,
        blank=True,
        verbose_name='Добавки',
        help_text='Только для пиццы'
    )
    sauce = models.ForeignKey(
        PizzaSauce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Соус',
        help_text='Только для пиццы и кальцоне'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')

    objects = CartQuerySet.as_manager()

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        ordering = ['-created_at']
        unique_together = [
            ['user', 'item', 'item_variant', 'board', 'sauce'],
        ]

    def __str__(self):
        size_info = ""
        if self.item_variant.size:
            size_info = f" | Размер: {self.item_variant.size.name}"
        elif self.item_variant.value:
            size_info = f" | {self.item_variant.value} {self.item_variant.get_unit_display()}"

        return f'Корзина {self.user.username} | Товар: {self.item.name}{size_info}'

    def calculate_cart_total(self):
        """
        Рассчитывает полную стоимость товара в корзине с учетом скидки на пиццу недели
        """
        # Базовая цена товара
        base_price = self.item_variant.price

        # Применяем скидку 10% если это пицца недели
        if self.item.is_weekly_special and self.item.category.name == "Пицца":
            base_price *= Decimal('0.9')  # 10% скидка

        # Цена борта (если есть)
        board_price = self.board.price if self.board else Decimal('0.00')

        # Сумма цен всех добавок
        addons_price = sum(addon.price for addon in self.addons.all()) if self.addons.exists() else Decimal('0.00')

        # Общая стоимость = (базовая цена + борт + добавки) * количество
        total_price = (base_price + board_price + addons_price) * self.quantity

        return total_price.quantize(Decimal(".01"))

    def get_size_display(self):
        """Возвращает отображаемое название размера/варианта"""
        if self.item_variant.size:
            return self.item_variant.size.name
        elif self.item_variant.value:
            return f"{self.item_variant.value} {self.item_variant.get_unit_display()}"
        return ""

    def get_full_description(self):
        """Возвращает полное описание товара в корзине"""
        desc = [self.item.name]

        size = self.get_size_display()
        if size:
            desc.append(size)

        if self.board:
            desc.append(f"Борт: {self.board.board.name}")

        if self.sauce:
            desc.append(f"Соус: {self.sauce.name}")

        if self.addons.exists():
            addons = ", ".join(a.addon.name for a in self.addons.all())
            desc.append(f"Добавки: {addons}")

        return " | ".join(desc)
