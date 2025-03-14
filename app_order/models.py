from django.db import models
from django.conf import settings
from app_cart.models import CartItem

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

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.id} | Пользователь: {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    item = models.ForeignKey('app_catalog.Item', on_delete=models.CASCADE, verbose_name='Товар')
    item_params = models.ForeignKey('app_catalog.ItemParams', on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    board = models.ForeignKey('app_catalog.BoardParams', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Борт')
    addons = models.ManyToManyField('app_catalog.AddonParams', blank=True, verbose_name='Добавки')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за единицу')

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return f'{self.item.name} | Заказ #{self.order.id}'