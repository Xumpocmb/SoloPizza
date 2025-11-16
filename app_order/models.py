from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from app_catalog.models import AddonParams, ProductVariant, BoardParams, PizzaSauce
from app_home.models import CafeBranch, Discount


class OrderManager(models.Manager):
    def get_order_totals(self, order_id):
        order = self.get_queryset().get(id=order_id)
        items = order.items.all()

        totals = {
            "subtotal": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "delivery_cost": self._calculate_delivery_cost(order),
            "items": [],
            "pickup_discount_applied": False,
        }

        for item in items:
            calculation = item.calculate_item_total()
            totals["subtotal"] += calculation["original_total"]
            totals["discount_amount"] += calculation["discount_amount"]

            if calculation["is_pickup_discount"]:
                totals["pickup_discount_applied"] = True

            totals["items"].append((item, calculation))

        order.subtotal = totals["subtotal"]
        order.discount_amount = totals["discount_amount"]
        order.delivery_cost = totals["delivery_cost"]
        order.total_price = totals["subtotal"] - totals["discount_amount"] + totals["delivery_cost"]
        order.save()

        return totals

    def _calculate_delivery_cost(self, order):
        """Динамический расчет стоимости доставки"""
        if order.delivery_type != "delivery":
            return Decimal("0.00")

        items = order.items.all().select_related("product__category")
        if not items:
            return Decimal("0.00")

        # Сумма товаров без учета доставки
        subtotal = sum(item.calculate_item_total()["final_total"] for item in items)

        # Проверяем, все ли товары в заказе относятся к фастфуду (за исключением "Напитки", "Соусы")
        is_all_fastfood = True
        for item in items:
            if item.product.category.name not in ["Фастфуд", "Соусы", "Напитки"]:
                is_all_fastfood = False
                break

        # Если все товары в заказе относятся к категории "Фастфуд" (за исключением "Напитки", "Соусы"),
        # применяем специальные правила расчета доставки
        if is_all_fastfood:
            # Сумма заказа меньше 25 руб: доставка 3 руб.
            # Сумма заказа больше или равна 25 руб: доставка бесплатная
            return Decimal("3.00") if subtotal < Decimal("25.00") else Decimal("0.00")
        else:
            # Для остальных случаев используем стандартную логику
            return Decimal("3.00") if subtotal < Decimal("20.00") else Decimal("0.00")


class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("confirmed", "Подтвержден"),
        ("cooking", "Готовится"),
        ("delivering", "Доставляется"),
        ("completed", "Завершен"),
        ("canceled", "Отменен"),
    ]

    PAYMENT_CHOICES = [
        ("cash", "Наличные"),
        ("card", "Карта"),
        # ('card_online', 'Карта онлайн'),
    ]

    DELIVERY_CHOICES = [
        ("pickup", "Самовывоз"),
        ("delivery", "Доставка"),
        ("cafe", "Зал")
    ]

    EDITABLE_STATUSES = ["new", "confirmed"]
    
    PARTNER_DISCOUNT_PERCENT = 15  # Процент скидки для партнеров

    session_key = models.CharField(max_length=40, verbose_name="Ключ сессии", db_index=True) # Added session_key field
    branch = models.ForeignKey(CafeBranch, on_delete=models.SET_NULL, verbose_name="Филиал", null=True)
    customer_name = models.CharField(max_length=255, verbose_name="Имя заказчика")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона", null=True, blank=True)
    address = models.TextField(verbose_name="Адрес доставки", null=True, blank=True)
    is_partner = models.BooleanField(default=False, verbose_name="Партнер")
    partner_discount_percent = models.PositiveIntegerField(default=10, verbose_name="Процент скидки партнера")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")

    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, verbose_name="Способ получения")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Способ оплаты")
    payment_status = models.BooleanField(default=True, verbose_name="Оплачено")
    
    ready_by = models.DateTimeField(verbose_name="Готов к", null=True, blank=True)
    delivery_by = models.DateTimeField(verbose_name="Доставка к", null=True, blank=True)

    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Сумма без скидок")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Сумма скидки")
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Стоимость доставки")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Итоговая сумма")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    objects = OrderManager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk and any(field in kwargs.get("update_fields", []) for field in ["delivery_type", "status"]):
            self.recalculate_totals()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    def recalculate_totals(self):
        """Пересчитывает и сохраняет итоговые суммы заказа"""
        Order.objects.get_order_totals(self.id)

    def is_editable(self):
        """Проверяет, можно ли редактировать заказ"""
        return self.status in self.EDITABLE_STATUSES

    def update_order_items(self):
        """Вызывается после изменения состава заказа"""
        self.recalculate_totals()

    @property
    def has_pickup_discount(self):
        """Проверяет, применена ли скидка на самовывоз"""
        if not hasattr(self, "_pickup_discount"):
            totals = Order.objects.get_order_totals(self.id)
            self._pickup_discount = totals["pickup_discount_applied"]
        return self._pickup_discount
        
    def add_item_from_cart(self, cart_item):
        """Добавляет товар из корзины в заказ"""
        order_item = OrderItem.objects.create(
            order=self,
            product=cart_item.item,  # Исправлено: cart_item.item вместо cart_item.product
            variant=cart_item.item_variant,  # Исправлено: cart_item.item_variant вместо cart_item.variant
            quantity=cart_item.quantity
        )
        
        # Копируем дополнительные параметры
        if cart_item.board1:
            order_item.board1 = cart_item.board1
            
        if cart_item.board2:
            order_item.board2 = cart_item.board2
                
        if cart_item.sauce:
            order_item.sauce = cart_item.sauce
            
        if cart_item.drink:
            order_item.drink = cart_item.drink
            
        order_item.save()
        
        # Добавляем добавки - исправлено для работы с ManyToManyField
        if cart_item.addons.exists():
            order_item.addons.set(cart_item.addons.all())
                
        self.recalculate_totals()
        return order_item


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey("app_catalog.Product", on_delete=models.PROTECT, verbose_name="Товар")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name="Вариант")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Скидка")
    board1 = models.ForeignKey(
        BoardParams,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Борт",
        related_name="orderitem_board1_set",
    )
    board2 = models.ForeignKey(
        BoardParams,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Борт",
        related_name="orderitem_board2_set",
    )
    sauce = models.ForeignKey(PizzaSauce, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Соус")
    addons = models.ManyToManyField(AddonParams, blank=True, verbose_name="Добавки")
    drink = models.CharField(max_length=100, null=True, blank=True, verbose_name="Напиток", help_text="Только для комбо наборов")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def get_size_display(self):
        if self.variant.size:
            return self.variant.size.name
        elif self.variant.value:
            return f"{self.variant.value} {self.variant.get_unit_display()}"
        return ""

    def get_full_description(self, include_price_info=False, base_unit_price=None, final_line_total=None):
        result = self.product.name

        size = self.get_size_display()
        if size:
            result += f"\n{size}"

        if self.board1:
            result += f"\nБорт 1: {self.board1.board.name}"
        if self.board2:
            result += f"\nБорт 2: {self.board2.board.name}"

        if self.sauce:
            result += f"\nСоус: {self.sauce.name}"

        if self.addons.exists():
            addons = ", ".join(a.addon.name for a in self.addons.all())
            result += f"\nДобавки: {addons}"
            
        if self.drink:
            result += f"\nНапиток: {self.drink}"
            
        if include_price_info and base_unit_price is not None and final_line_total is not None:
            result += f"\nКол-во: {self.quantity}"
            result += f"\nЦена: {base_unit_price:.2f}"
            result += f"\nСумма: {final_line_total:.2f}"

        return result

    def calculate_item_total(self):
        base_price = self.variant.price
        quantity = self.quantity

        # Рассчитываем стоимость допов (бортов и добавок)
        board1_price = self.board1.price if self.board1 else Decimal("0")
        board2_price = self.board2.price if self.board2 else Decimal("0")
        addons_price = sum(addon.price for addon in self.addons.all()) if self.addons.exists() else Decimal("0")

        # Стоимость дополнений (не участвует в скидке)
        additions_total = (board1_price + board2_price + addons_price) * quantity

        # Изначально скидка 0
        discount_amount = Decimal("0")
        discount_percent = Decimal("0")
        is_pickup_discount = False
        is_weekly_pizza_discount = False
        is_partner_discount = False

        # Проверяем условия для скидки
        if self.product.category.name == "Пицца":
            # Если активирована скидка партнера, применяем только её
            if self.order.is_partner:
                # Используем значение процента скидки из заказа
                discount_percent = Decimal(str(self.order.partner_discount_percent))
                # Скидка применяется только к базовой цене товара
                discount_amount = (base_price * (discount_percent / Decimal("100"))) * quantity
                is_partner_discount = True
            # Иначе применяем обычные скидки
            else:
                # Скидка на самовывоз
                if self.order.delivery_type == "pickup":
                    # Получаем скидку "Самовывоз" из базы данных
                    try:
                        pickup_discount = Discount.objects.get(slug="pickup")
                        discount_percent = Decimal(str(pickup_discount.percent))
                        discount_amount = (base_price * (discount_percent / Decimal("100"))) * quantity
                        is_pickup_discount = True
                    except Discount.DoesNotExist:
                        try:
                            pickup_discount = Discount.objects.get(name="Самовывоз")
                            discount_percent = Decimal(str(pickup_discount.percent))
                            discount_amount = (base_price * (discount_percent / Decimal("100"))) * quantity
                            is_pickup_discount = True
                        except Discount.DoesNotExist:
                            pass

                    # Дополнительная скидка на пиццу недели (только при самовывозе и только для размера "32")
                    if self.product.is_weekly_special and self.variant.size and self.variant.size.name == "32":
                        try:
                            weekly_pizza_discount = Discount.objects.get(slug="weekly-pizza")
                            weekly_discount_percent = Decimal(str(weekly_pizza_discount.percent))
                            weekly_discount_amount = (base_price * (weekly_discount_percent / Decimal("100"))) * quantity
                            discount_amount = weekly_discount_amount
                            discount_percent = weekly_discount_percent
                            is_weekly_pizza_discount = True
                        except Discount.DoesNotExist:
                            try:
                                weekly_pizza_discount = Discount.objects.get(name="Пицца недели")
                                weekly_discount_percent = Decimal(str(weekly_pizza_discount.percent))
                                weekly_discount_amount = (base_price * (weekly_discount_percent / Decimal("100"))) * quantity
                                discount_amount = weekly_discount_amount
                                discount_percent = weekly_discount_percent
                                is_weekly_pizza_discount = True
                            except Discount.DoesNotExist:
                                # Если скидка не найдена, используем значение по умолчанию 20%
                                weekly_discount_percent = Decimal("20")
                                weekly_discount_amount = (base_price * (weekly_discount_percent / Decimal("100"))) * quantity
                                discount_amount = weekly_discount_amount
                                discount_percent = weekly_discount_percent
                                is_weekly_pizza_discount = True

        # Итоговые суммы
        original_total = (base_price + board1_price + board2_price + addons_price) * quantity
        # Скидка применяется только к базовой цене товара, не к бортам и добавкам
        # При партнерской скидке используется значение из заказа (partner_discount_percent)
        discounted_base_price = base_price * (1 - discount_percent / Decimal("100"))
        final_total = (discounted_base_price * quantity) + additions_total

        return {
            "original_total": original_total.quantize(Decimal(".01")),
            "final_total": final_total.quantize(Decimal(".01")),
            "discount_amount": discount_amount.quantize(Decimal(".01")),
            "discount_percent": discount_percent,
            "is_weekly_pizza": is_weekly_pizza_discount,
            "is_pickup_discount": is_pickup_discount,
            "is_partner_discount": is_partner_discount,
        }


@receiver(post_save, sender=OrderItem)
def update_order_on_item_change(sender, instance, **kwargs):
    instance.order.update_order_items()


@receiver(post_delete, sender=OrderItem)
def update_order_on_item_delete(sender, instance, **kwargs):
    instance.order.update_order_items()


@receiver(m2m_changed, sender=OrderItem.addons.through)
def update_order_on_addons_change(sender, instance, action, **kwargs):
    """Обновляет итоги заказа при изменении добавок в позиции заказа"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.order.update_order_items()
