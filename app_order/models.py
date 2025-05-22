from django.db import models
from django.conf import settings
from app_cart.models import CartItem
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from decimal import Decimal



class OrderManager(models.Manager):
    def calculate_total_price(self, order_id):
        """
        Рассчитывает общую стоимость заказа, включая доставку.
        """
        order = self.get(id=order_id)
        items_total = sum(
            item.calculate_item_total_price() for item in order.items.all()
        )

        # Стоимость доставки
        delivery_cost = (
            Decimal(3) if order.delivery_method == "delivery" and items_total < Decimal(20) else Decimal(0)
        )

        # Общая стоимость заказа
        total_price = items_total + delivery_cost

        # Обновляем поля заказа
        order.total_price = total_price
        order.delivery_cost = delivery_cost
        order.save(update_fields=["total_price", "delivery_cost"])

        return total_price

    def get_order_summary(self, order_id):
        """
        Возвращает краткое описание заказа (статус, общая стоимость и т.д.).
        """
        order = self.get(id=order_id)
        return {
            "id": order.id,
            "status": dict(order.STATUS_CHOICES).get(order.status),
            "total_price": order.total_price,
            "delivery_cost": order.delivery_cost,
            "items_count": order.items.count(),
        }


class OrderItemManager(models.Manager):
    def calculate_item_total_price(self, order_item_id):
        """
        Рассчитывает полную стоимость товара, включая добавки и борт.
        """
        order_item = self.get(id=order_item_id)

        base_price = order_item.price * order_item.quantity
        addons_price = self.calculate_total_addon_price(order_item)
        board_price = order_item.board.price if order_item.board else Decimal(0)

        # Итоговая стоимость без скидки
        total_without_discount = base_price + board_price + addons_price

        # Рассчитываем скидку
        discount = self.calculate_discount(order_item)

        # Итоговая стоимость с учетом скидки
        total_with_discount = total_without_discount - (discount or Decimal(0))
        return total_with_discount.quantize(Decimal(".01"))

    def calculate_total_addon_price(self, order_item):
        """
        Рассчитывает общую стоимость всех добавок.
        """
        addons = order_item.addons.all()
        addon_prices = [addon.price for addon in addons]
        return sum(addon_prices)

    def calculate_discount(self, order_item):
        """
        Рассчитывает скидку на товар.
        """
        item_discount = Decimal(0)
        item_discount_percent = Decimal(0)

        # Скидка только для пиццы
        if order_item.item.category.name == "Пицца":
            # Если доставка - самовывоз
            if order_item.order.delivery_method == "pickup":
                if order_item.item.is_weekly_special and order_item.item_params.size.size == 32:
                    # Акция "Пицца недели" (20% скидка при самовывозе)
                    weekly_discount_percent = Decimal("20.0")
                    item_discount = (
                        order_item.price * (weekly_discount_percent / Decimal("100"))
                    ) * order_item.quantity
                    item_discount_percent = weekly_discount_percent
                else:
                    # Скидка 10% для самовывоза
                    pickup_discount_percent = Decimal("10.0")
                    item_discount = (
                        order_item.price * (pickup_discount_percent / Decimal("100"))
                    ) * order_item.quantity
                    item_discount_percent = pickup_discount_percent
            elif order_item.order.partner_discount:
                # Скидка 10% для партнеров
                partner_discount_percent = Decimal("10.0")
                item_discount = (
                    order_item.price * (partner_discount_percent / Decimal("100"))
                ) * order_item.quantity
                item_discount_percent = partner_discount_percent

        # Обновляем скидку
        order_item.item_discount = item_discount
        order_item.item_discount_percent = item_discount_percent
        order_item.save(update_fields=["item_discount", "item_discount_percent"])

        return item_discount


class Order(models.Model):
    objects = OrderManager()

    STATUS_CHOICES = [
        ("created", "Создан"),
        ("pending", "В обработке"),
        ("confirmed", "Подтвержден"),
        ("shipped", "Отправлен"),
        ("delivered", "Доставлен"),
        ("cancelled", "Отменен"),
    ]

    DELIVERY_METHOD_CHOICES = [
        ("pickup", "Самовывоз"),
        ("delivery", "Доставка"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created",
        verbose_name="Статус заказа",
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Общая сумма"
    )
    latitude = models.FloatField(verbose_name="Широта", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Долгота", null=True, blank=True)
    address = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Адрес"
    )
    apartment = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Квартира"
    )
    entrance = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Подъезд"
    )
    floor = models.CharField(max_length=10, blank=True, null=True, verbose_name="Этаж")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    cafe_branch = models.ForeignKey(
        "app_home.CafeBranch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Филиал",
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        default="pickup",
        verbose_name="Метод доставки",
        null=True,
        blank=True,
    )
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal(0),
        verbose_name="Стоимость доставки",
        null=True,
        blank=True,
    )
    partner_discount = models.BooleanField(
        default=False, verbose_name="Партнерский скидка"
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} | Пользователь: {self.user.username}"

    def calculate_total_price(self) -> Decimal:
        """
        Рассчитывает общую стоимость заказа, включая доставку.
        """
        if not hasattr(self, '_is_calculating'):
            self._is_calculating = True
            try:
                items_total = sum(
                    item.calculate_item_total_price() for item in self.items.all()
                )

                # Стоимость доставки
                self.delivery_cost = (
                    Decimal(3)
                    if self.delivery_method == "delivery" and items_total < Decimal(20)
                    else Decimal(0)
                )

                # Общая стоимость заказа
                self.total_price = items_total + self.delivery_cost
                self.save(update_fields=["total_price", "delivery_cost"])
                return self.total_price
            finally:
                del self._is_calculating

    def get_status_display(self):
        """Возвращает человекочитаемое описание статуса."""
        return dict(self.STATUS_CHOICES).get(self.status, "Неизвестный статус")


class OrderItem(models.Model):
    objects = OrderItemManager()

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ"
    )
    item = models.ForeignKey(
        "app_catalog.Item", on_delete=models.CASCADE, verbose_name="Товар"
    )
    item_params = models.ForeignKey(
        "app_catalog.ItemParams", on_delete=models.CASCADE, verbose_name="Размер"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    sauce = models.ForeignKey(
        "app_catalog.PizzaSauce",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Соус",
    )
    board = models.ForeignKey(
        "app_catalog.BoardParams",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Борт",
    )
    addons = models.ManyToManyField(
        "app_catalog.AddonParams", blank=True, verbose_name="Добавки"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Цена за единицу"
    )
    item_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal(0), verbose_name="Скидка"
    )
    item_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(0),
        verbose_name="Процент скидки",
    )

    class Meta:
        db_table = "order_items"
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def __str__(self):
        return f"{self.item.name} | Заказ #{self.order.id}"

    def get_addons_display(self):
        """Возвращает строку с названиями всех добавок."""
        return (
            ", ".join(addon.addon.name for addon in self.addons.all()) or "Нет добавок"
        )

    def calculate_item_total_price(self):
        """
        Рассчитывает полную стоимость товара, включая добавки и борт.
        """
        if not hasattr(self, '_is_calculating'):
            self._is_calculating = True
            try:
                base_price = self.price * self.quantity
                addons_price = self.calculate_total_addon_price()
                board_price = self.board.price if self.board else 0

                # Итоговая стоимость без скидки
                total_without_discount = (
                    base_price + board_price + addons_price
                ) * self.quantity

                # Рассчитываем скидку
                self.calculate_discount()

                # Итоговая стоимость с учетом скидки
                total_with_discount = total_without_discount - (
                    self.item_discount or Decimal(0)
                )
                return total_with_discount.quantize(Decimal(".01"))
            finally:
                del self._is_calculating

    def calculate_total_addon_price(self):
        """
        Рассчитывает общую стоимость всех добавок.
        """
        addons = self.addons.all()
        addon_prices = [addon.price for addon in addons]
        total_addons_price = sum(addon_prices)
        return total_addons_price

    def calculate_discount(self):
        """
        Рассчитывает скидку на товар.
        """
        if not hasattr(self, '_is_calculating'):
            self._is_calculating = True
            try:
                self.item_discount = Decimal(0)
                self.item_discount_percent = Decimal(0)

                # Скидка только для пиццы
                if self.item.category.name == "Пицца":
                    # Если доставка - самовывоз
                    if self.order.delivery_method == "pickup":
                        if self.item.is_weekly_special and self.item_params.size.size == 32:
                            # Акция "Пицца недели" (20% скидка при самовывозе)
                            weekly_discount_percent = Decimal("20.0")
                            self.item_discount = (
                                self.price * (weekly_discount_percent / Decimal("100"))
                            ) * self.quantity
                            self.item_discount_percent = weekly_discount_percent
                        else:
                            # Скидка 10% для самовывоза
                            pickup_discount_percent = Decimal("10.0")
                            self.item_discount = (
                                self.price * (pickup_discount_percent / Decimal("100"))
                            ) * self.quantity
                            self.item_discount_percent = pickup_discount_percent
                    elif self.order.partner_discount:
                        # Скидка 10% для партнеров
                        partner_discount_percent = Decimal("10.0")
                        self.item_discount = (
                            self.price * (partner_discount_percent / Decimal("100"))
                        ) * self.quantity
                        self.item_discount_percent = partner_discount_percent

                # Сохраняем скидку
                self.save(update_fields=["item_discount", "item_discount_percent"])
            finally:
                del self._is_calculating


# @receiver(post_save, sender=OrderItem)
# @receiver(post_delete, sender=OrderItem)
# def update_order_total_price(sender, instance, **kwargs):
#     """
#     Автоматически обновляет total_price заказа при изменении OrderItem.
#     """
#     instance.order.calculate_total_price()


# @receiver(m2m_changed, sender=OrderItem.addons.through)
# def update_order_total_price_on_addons_change(sender, instance, action, **kwargs):
#     """
#     Автоматически обновляет total_price заказа при изменении добавок.
#     """
#     if action in ["post_add", "post_remove", "post_clear"]:
#         instance.order.calculate_total_price()


# @receiver(post_save, sender=OrderItem)
# def update_order_total_price_on_board_change(sender, instance, **kwargs):
#     """
#     Автоматически обновляет total_price заказа при изменении борта.
#     """
#     if "board" in instance.get_deferred_fields():
#         instance.order.calculate_total_price()
