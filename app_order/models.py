from decimal import Decimal
from contextlib import contextmanager
import json
import threading
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from app_catalog.models import AddonParams, ProductVariant, BoardParams, PizzaSauce
from django.contrib.auth import get_user_model # Import get_user_model

User = get_user_model() # Get the User model
from app_home.models import CafeBranch, Discount


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


class DiscountCache:
    """Кэш скидок на время одного пересчёта: иначе запрос на скидку уходит на каждую позицию."""

    def __init__(self):
        self._discounts = {}

    def find(self, slug=None, name=None):
        key = slug or name
        if key not in self._discounts:
            try:
                if slug:
                    self._discounts[key] = Discount.objects.get(slug=slug)
                else:
                    self._discounts[key] = Discount.objects.get(name=name)
            except Discount.DoesNotExist:
                self._discounts[key] = None
        return self._discounts[key]

    def percent(self, slug=None, name=None):
        discount = self.find(slug=slug, name=name)
        return discount.percent if discount is not None else None


_recalculation_state = threading.local()


@contextmanager
def suspended_order_totals():
    """Откладывает пересчёт итогов на время массового изменения позиций заказа."""
    previous = getattr(_recalculation_state, "suspended", False)
    _recalculation_state.suspended = True
    try:
        yield
    finally:
        _recalculation_state.suspended = previous


def order_recalculation_suspended():
    return getattr(_recalculation_state, "suspended", False)


class OrderManager(models.Manager):
    def get_order_totals(self, order):
        """Считает итоги заказа, ничего не сохраняя. Принимает заказ или его id."""
        if not isinstance(order, Order):
            order = self.get_queryset().get(id=order)

        discounts = DiscountCache()
        item_calculations = [
            (item, item.calculate_item_total(discounts=discounts)) for item in self._order_items(order)
        ]

        totals = {
            "subtotal": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "delivery_cost": self._calculate_delivery_cost(order, item_calculations),
            "items": item_calculations,
            "pickup_discount_applied": False,
        }

        for _, calculation in item_calculations:
            totals["subtotal"] += calculation["original_total"]
            totals["discount_amount"] += calculation["discount_amount"]

            if calculation["is_pickup_discount"]:
                totals["pickup_discount_applied"] = True

        totals["total_price"] = totals["subtotal"] - totals["discount_amount"] + totals["delivery_cost"]

        return totals

    def _order_items(self, order):
        """Позиции заказа вместе со всем, что нужно расчёту, если они не загружены заранее."""
        if "items" in getattr(order, "_prefetched_objects_cache", {}):
            return order.items.all()

        return order.items.select_related("product__category", "variant__size", "board1", "board2").prefetch_related("addons")

    def _calculate_delivery_cost(self, order, item_calculations=None):
        """Динамический расчет стоимости доставки"""
        if order.delivery_type != "delivery":
            return Decimal("0.00")

        if item_calculations is None:
            item_calculations = [
                (item, item.calculate_item_total())
                for item in order.items.all().select_related("product__category")
            ]

        if not item_calculations:
            return Decimal("0.00")

        # Сумма товаров без учета доставки
        subtotal = sum(calculation["final_total"] for _, calculation in item_calculations)

        # Проверяем, все ли товары в заказе относятся к фастфуду (по опции категории)
        is_all_fastfood = all(
            item.product.category.is_fastfood
            for item, _ in item_calculations
        )

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
        ("new", _("Новый")),
        ("confirmed", _("Подтвержден")),
        ("cooking", _("Готовится")),
        ("delivering", _("Доставляется")),
        ("completed", _("Завершен")),
        ("canceled", _("Отменен")),
    ]

    PAYMENT_CHOICES = [
        ("cash", _("Наличные")),
        ("card", _("Карта")),
        ('noname', _('Безналичный расчет')),
        ('split', _('Раздельная оплата')),
    ]

    DELIVERY_CHOICES = [
        ("pickup", _("Самовывоз")),
        ("delivery", _("Доставка")),
        ("cafe", _("Зал"))
    ]

    EDITABLE_STATUSES = ["new", "confirmed"]
    
    PARTNER_DISCOUNT_PERCENT = 15  # Процент скидки для партнеров

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    session_key = models.CharField(max_length=40, verbose_name="Ключ сессии", db_index=True, null=True, blank=True)
    guest_token = models.CharField(max_length=40, verbose_name="Гостевой токен", db_index=True, null=True, blank=True)
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

    # Fields for split payment
    cash_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Сумма наличными", blank=True)
    card_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Сумма картой", blank=True)
    noname_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Сумма безналично", blank=True)
    
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
        return f"Заказ #{self.print_number} от {self.created_at.strftime('%d.%m.%Y')}"

    @property
    def print_number(self):
        """Номер заказа для печати чека: цифра в чеке филиала + id заказа (3 цифры)."""
        order_part = f"{self.id:03d}"
        branch = self.branch
        branch_part = branch.check_digit if branch is not None and branch.check_digit is not None else 0
        return f"{branch_part}{order_part}"

    def recalculate_totals(self):
        """Пересчитывает и сохраняет итоговые суммы заказа"""
        totals = Order.objects.get_order_totals(self)

        self.subtotal = totals["subtotal"]
        self.discount_amount = totals["discount_amount"]
        self.delivery_cost = totals["delivery_cost"]
        self.total_price = totals["total_price"]
        self.save()

        return totals

    def is_editable(self):
        """Проверяет, можно ли редактировать заказ"""
        return self.status in self.EDITABLE_STATUSES

    def get_split_payment_total(self):
        """Возвращает общую сумму раздельной оплаты"""
        return self.cash_amount + self.card_amount + self.noname_amount

    def is_split_payment_valid(self):
        """Проверяет, совпадает ли сумма раздельной оплаты с итоговой суммой заказа"""
        if self.payment_method == 'split':
            return abs(self.get_split_payment_total() - self.total_price) < Decimal('0.01')
        return True

    def get_payment_method_display(self):
        """Возвращает отображаемое имя способа оплаты"""
        payment_method_dict = dict(self.PAYMENT_CHOICES)
        return payment_method_dict.get(self.payment_method, self.payment_method)

    def update_order_items(self):
        """Вызывается после изменения состава заказа"""
        self.recalculate_totals()

    @property
    def has_pickup_discount(self):
        """Проверяет, применена ли скидка на самовывоз"""
        if not hasattr(self, "_pickup_discount"):
            self._pickup_discount = Order.objects.get_order_totals(self)["pickup_discount_applied"]
        return self._pickup_discount


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

    def set_total_cache(self, calculation):
        """Подставляет уже посчитанный результат, чтобы не считать его повторно."""
        self._item_total_cache = calculation

    def clear_total_cache(self):
        self.__dict__.pop("_item_total_cache", None)

    def calculate_item_total(self, discounts=None):
        cached = getattr(self, "_item_total_cache", None)
        if cached is not None:
            return cached

        if discounts is None:
            discounts = DiscountCache()

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
        if getattr(self.product.category, 'applies_pizza_discounts', False):
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
                    pickup_percent = discounts.percent(slug="pickup")
                    if pickup_percent is None:
                        pickup_percent = discounts.percent(name="Самовывоз")
                    if pickup_percent is not None:
                        discount_percent = Decimal(str(pickup_percent))
                        discount_amount = (base_price * (discount_percent / Decimal("100"))) * quantity
                        is_pickup_discount = True

                    # Дополнительная скидка на пицца недели (только при самовывозе и только для размера "32")
                    if self.product.is_weekly_special and self.variant.size and self.variant.size.name == "32":
                        weekly_percent = discounts.percent(slug="weekly-pizza")
                        if weekly_percent is None:
                            weekly_percent = discounts.percent(name="Пицца недели")
                        if weekly_percent is None:
                            # Если скидка не найдена, используем значение по умолчанию 20%
                            weekly_percent = 20
                        weekly_discount_percent = Decimal(str(weekly_percent))
                        discount_amount = (base_price * (weekly_discount_percent / Decimal("100"))) * quantity
                        discount_percent = weekly_discount_percent
                        is_weekly_pizza_discount = True

        # Итоговые суммы
        original_total = (base_price + board1_price + board2_price + addons_price) * quantity
        # Скидка применяется только к базовой цене товара, не к бортам и добавкам
        # При партнерской скидке используется значение из заказа (partner_discount_percent)
        discounted_base_price = base_price * (1 - discount_percent / Decimal("100"))
        final_total = (discounted_base_price * quantity) + additions_total

        calculation = {
            "original_total": original_total.quantize(Decimal(".01")),
            "final_total": final_total.quantize(Decimal(".01")),
            "discount_amount": discount_amount.quantize(Decimal(".01")),
            "discount_percent": discount_percent,
            "is_weekly_pizza": is_weekly_pizza_discount,
            "is_pickup_discount": is_pickup_discount,
            "is_partner_discount": is_partner_discount,
        }
        self.set_total_cache(calculation)

        return calculation


@receiver(post_save, sender=OrderItem)
def update_order_on_item_change(sender, instance, **kwargs):
    instance.clear_total_cache()
    if order_recalculation_suspended():
        return
    instance.order.update_order_items()


@receiver(post_delete, sender=OrderItem)
def update_order_on_item_delete(sender, instance, **kwargs):
    instance.clear_total_cache()
    if order_recalculation_suspended():
        return
    instance.order.update_order_items()


@receiver(m2m_changed, sender=OrderItem.addons.through)
def update_order_on_addons_change(sender, instance, action, **kwargs):
    """Обновляет итоги заказа при изменении добавок в позиции заказа"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.clear_total_cache()
        if order_recalculation_suspended():
            return
        instance.order.update_order_items()


class OrderStatistic(models.Model):
    """Модель для хранения статистики по заказам за день."""
    date = models.DateField(unique=True, verbose_name="Дата")
    orders_count = models.PositiveIntegerField(verbose_name="Количество заказов")
    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Сумма (наличные)")
    total_card = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Сумма (карта)")
    total_noname = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Сумма (безнал)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итоговая сумма")
    sold_items = models.JSONField(default=dict, verbose_name="Проданные товары", encoder=DecimalEncoder)

    class Meta:
        verbose_name = "Статистика по заказам"
        verbose_name_plural = "Статистика по заказам"
        ordering = ['-date']

    def __str__(self):
        return f"Статистика за {self.date.strftime('%d.%m.%Y')}"
