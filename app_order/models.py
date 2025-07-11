from decimal import Decimal
from django.db import models
from django.conf import settings
from app_catalog.models import AddonParams, ProductVariant, BoardParams, PizzaSauce, PizzaAddon


class OrderManager(models.Manager):
    def get_order_totals(self, order_id):
        order = self.get_queryset().get(id=order_id)
        items = order.items.all()

        totals = {"subtotal": Decimal("0.00"), "discount_amount": Decimal("0.00"), "total_price": Decimal("0.00"), "items": []}

        for item in items:
            calculation = item.calculate_item_total()
            totals["subtotal"] += calculation["original_total"]
            totals["discount_amount"] += calculation["discount_amount"]
            totals["total_price"] += calculation["final_total"]
            totals["items"].append((item, calculation))

        return totals


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
    ]

    EDITABLE_STATUSES = ["new", "confirmed"]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
        verbose_name="Пользователь",
    )
    customer_name = models.CharField(max_length=255, verbose_name="Имя заказчика")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")
    address = models.TextField(verbose_name="Адрес доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")

    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, verbose_name="Способ получения")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Способ оплаты")
    payment_status = models.BooleanField(default=True, verbose_name="Оплачено")

    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    objects = OrderManager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    def recalculate_totals(self):
        """Пересчитывает и сохраняет итоговые суммы заказа"""
        totals = Order.objects.get_order_totals(self.id)
        self.subtotal = totals["subtotal"]
        self.discount_amount = totals["discount_amount"]
        self.total_price = totals["total_price"]
        self.save()

    def is_editable(self):
        """Проверяет, можно ли редактировать заказ"""
        return self.status in self.EDITABLE_STATUSES


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey("app_catalog.Product", on_delete=models.PROTECT, verbose_name="Товар")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name="Вариант")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
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

    def get_full_description(self):
        desc = [self.product.name]

        size = self.get_size_display()
        if size:
            desc.append(size)

        if self.board1:
            desc.append(f"Борт 1: {self.board1.board.name}")
        if self.board2:
            desc.append(f"Борт 2: {self.board2.board.name}")

        if self.sauce:
            desc.append(f"Соус: {self.sauce.name}")

        if self.addons.exists():
            addons = ", ".join(a.addon.name for a in self.addons.all())
            desc.append(f"Добавки: {addons}")

        return " | ".join(desc)

    def calculate_item_total(self):
        base_price = self.variant.price
        quantity = self.quantity

        board1_price = self.board1.price if self.board1 else Decimal("0")
        board2_price = self.board2.price if self.board2 else Decimal("0")
        addons_price = sum(addon.price for addon in self.addons.all()) if self.addons.exists() else Decimal("0")

        original_total = (base_price + board1_price + board2_price + addons_price) * quantity

        is_weekly_pizza = self.product.is_weekly_special and getattr(self.product.category, "name", "") == "Пицца"
        discount_amount = (base_price * quantity * Decimal("0.1")) if is_weekly_pizza else Decimal("0")

        final_total = original_total - discount_amount

        return {
            "original_total": original_total.quantize(Decimal(".01")),
            "final_total": final_total.quantize(Decimal(".01")),
            "discount_amount": discount_amount.quantize(Decimal(".01")),
            "is_weekly_pizza": is_weekly_pizza,
        }

