from django.db import models
from django.conf import settings
from app_cart.models import CartItem
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('pending', 'В обработке'),
        ('confirmed', 'Подтвержден'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name='Статус заказа')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая сумма')
    latitude = models.FloatField(verbose_name='Широта', null=True, blank=True)
    longitude = models.FloatField(verbose_name='Долгота', null=True, blank=True)
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name='Адрес')
    apartment = models.CharField(max_length=10, blank=True, null=True, verbose_name='Квартира')
    entrance = models.CharField(max_length=10, blank=True, null=True, verbose_name='Подъезд')
    floor = models.CharField(max_length=10, blank=True, null=True, verbose_name='Этаж')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    cafe_branch = models.ForeignKey('app_home.CafeBranch', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Филиал')

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.id} | Пользователь: {self.user.username}'

    def calculate_total_price(self):
        """
        Рассчитывает общую стоимость заказа на основе всех товаров.
        """
        total = sum(
            item.calculate_total_price() for item in self.items.all()
        )
        print(f"Debug: Order ID={self.id}")
        print(f"  Items total: {total}")
        return total

    def update_total_price(self):
        """
        Обновляет поле total_price текущим значением.
        """
        self.total_price = self.calculate_total_price()
        self.save(update_fields=['total_price'])

    def get_status_display(self):
        """Возвращает человекочитаемое описание статуса."""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестный статус')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    item = models.ForeignKey('app_catalog.Item', on_delete=models.CASCADE, verbose_name='Товар')
    item_params = models.ForeignKey('app_catalog.ItemParams', on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    sauce = models.ForeignKey('app_catalog.PizzaSauce', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Соус')
    board = models.ForeignKey('app_catalog.BoardParams', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Борт')
    addons = models.ManyToManyField('app_catalog.AddonParams', blank=True, verbose_name='Добавки')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за единицу')

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return f'{self.item.name} | Заказ #{self.order.id}'

    def get_addons_display(self):
        """Возвращает строку с названиями всех добавок."""
        return ', '.join(addon.addon.name for addon in self.addons.all()) or 'Нет добавок'

    def calculate_total_price(self):
        """
        Рассчитывает полную стоимость товара, включая добавки и борт.
        """
        base_price = self.price * self.quantity
        addons_price = self.calculate_total_addon_price()  # Стоимость добавок для одного экземпляра
        board_price = self.board.price if self.board else 0

        # Итоговая стоимость: базовая цена + борт + добавки, все умноженные на количество
        total = (base_price + board_price + addons_price) * self.quantity

        print(f"Debug: OrderItem ID={self.id}")
        print(f"  Base price: {base_price}")
        print(f"  Addons price: {addons_price}")
        print(f"  Board price: {board_price}")
        print(f"  Quantity: {self.quantity}")
        print(f"  Total: {total}")

        return total

    def calculate_total_addon_price(self):
        """
        Рассчитывает общую стоимость всех добавок.
        """
        addons = self.addons.all()
        addon_prices = [addon.price for addon in addons]
        total_addons_price = sum(addon_prices)

        print(f"Debug: OrderItem ID={self.id}")
        print(f"  Addons: {[addon.addon.name for addon in addons]}")
        print(f"  Addon prices: {addon_prices}")
        print(f"  Total addons price: {total_addons_price}")

        return total_addons_price


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total_price(sender, instance, **kwargs):
    """
    Автоматически обновляет total_price заказа при изменении OrderItem.
    """
    instance.order.update_total_price()

@receiver(m2m_changed, sender=OrderItem.addons.through)
def update_order_total_price_on_addons_change(sender, instance, action, **kwargs):
    """
    Автоматически обновляет total_price заказа при изменении добавок.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.order.update_total_price()

@receiver(post_save, sender=OrderItem)
def update_order_total_price_on_board_change(sender, instance, **kwargs):
    """
    Автоматически обновляет total_price заказа при изменении борта.
    """
    if 'board' in instance.get_deferred_fields():
        instance.order.update_total_price()