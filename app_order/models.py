from django.db import models
from django.conf import settings
from app_catalog.models import ProductVariant, BoardParams, PizzaSauce, PizzaAddon


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('cooking', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        # ('card_online', 'Карта онлайн'),
    ]

    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка'),
    ]

    EDITABLE_STATUSES = ['new', 'confirmed']

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name='Пользователь'
    )
    customer_name = models.CharField(max_length=255, verbose_name='Имя заказчика')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        verbose_name='Способ получения'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        verbose_name='Способ оплаты'
    )
    payment_status = models.BooleanField(default=True, verbose_name='Оплачено')
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая сумма'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки'
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма без скидки'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий к заказу')
    phone_number = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.TextField(verbose_name='Адрес доставки')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    def get_final_price(self):
        """Возвращает итоговую цену с учетом скидки"""
        return self.total_price

    def is_editable(self):
        """Проверяет, можно ли редактировать заказ"""
        return self.status in self.EDITABLE_STATUSES

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        'app_catalog.Product',
        on_delete=models.PROTECT,
        verbose_name='Товар'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        verbose_name='Вариант'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )
    board = models.ForeignKey(
        BoardParams,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Борт'
    )
    sauce = models.ForeignKey(
        PizzaSauce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Соус'
    )
    is_weekly_special = models.BooleanField(
        default=False,
        verbose_name='Акция "Пицца недели"'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки'
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def get_final_price(self):
        """Возвращает итоговую цену позиции с учетом скидки"""
        return (self.price * self.quantity) - self.discount_amount

    def is_editable(self):
        """Можно ли редактировать этот товар в заказе"""
        return self.order.status in self.order.EDITABLE_STATUSES

class OrderItemAddon(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='addons',
        verbose_name='Позиция заказа'
    )
    addon = models.ForeignKey(
        PizzaAddon,
        on_delete=models.PROTECT,
        verbose_name='Добавка'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена'
    )

    class Meta:
        verbose_name = 'Добавка к позиции'
        verbose_name_plural = 'Добавки к позициям'

    def __str__(self):
        return f"{self.addon.name} для {self.order_item.product.name}"
