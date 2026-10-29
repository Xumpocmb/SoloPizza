from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce


class CartItemManager(models.Manager):
    def total_quantity(self, session_key):
        return self.filter(session_key=session_key).aggregate(total=Sum("quantity"))["total"] or 0

    def get_cart_totals(self, session_key):
        cart_items = self.filter(session_key=session_key).select_related("item", "item_variant", "sauce", "board1", "board2").prefetch_related("addons")

        totals = {"total_price": Decimal("0.00"), "total_original_price": Decimal("0.00"), "total_discount": Decimal("0.00"), "items": []}

        for item in cart_items:
            calculation = item.calculate_cart_item_total()
            totals["total_price"] += calculation["final_total"]
            totals["total_original_price"] += calculation["original_total"]
            totals["total_discount"] += calculation["discount_amount"]
            totals["items"].append((item, calculation))

        return totals


class CartItem(models.Model):
    session_key = models.CharField(max_length=40, verbose_name="Ключ сессии", db_index=True)
    item = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    item_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, verbose_name="Вариант товара", help_text="Выбранный размер/вариант товара", null=True, blank=True
    )  # TODO: remove null and blank
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    board1 = models.ForeignKey(
        BoardParams, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Борт1", help_text="Только для пиццы", related_name="cartitem_board1_set"
    )
    board2 = models.ForeignKey(
        BoardParams, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Борт2", help_text="Только для пиццы", related_name="cartitem_board2_set"
    )
    addons = models.ManyToManyField(AddonParams, blank=True, verbose_name="Добавки", help_text="Только для пиццы")
    sauce = models.ForeignKey(PizzaSauce, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Соус", help_text="Только для пиццы и кальцоне")
    drink = models.CharField(max_length=100, null=True, blank=True, verbose_name="Напиток", help_text="Только для комбо наборов")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Дата обновления")

    objects = CartItemManager()

    class Meta:
        db_table = "cart_items"
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        ordering = ["-created_at"]
        unique_together = [
            ["session_key", "item", "item_variant", "board1", "board2", "sauce"],
        ]

    def __str__(self):
        size_info = ""
        if self.item_variant.size:
            size_info = f" | Размер: {self.item_variant.size.name}"
        elif self.item_variant.value:
            size_info = f" | {self.item_variant.value} {self.item_variant.get_unit_display()}"

        return f"Корзина {self.session_key} | Товар: {self.item.name}{size_info}"

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

        # Добавляем информацию о бортах для пиццы и комбо
        if self.board1 or self.board2:
            boards = []
            if self.board1:
                boards.append(f"Борт 1: {self.board1.board.name}")
            if self.board2:
                boards.append(f"Борт 2: {self.board2.board.name}")
            desc.append(" | ".join(boards))

        if self.sauce:
            desc.append(f"Соус: {self.sauce.name}")

        if self.addons.exists():
            addons = ", ".join(a.addon.name for a in self.addons.all())
            desc.append(f"Добавки: {addons}")
            
        if self.drink:
            desc.append(f"Напиток: {self.drink}")

        return " | ".join(desc)

    def calculate_cart_item_total(self):
        base_price = self.item_variant.price
        quantity = self.quantity

        board1_price = self.board1.price if self.board1 else Decimal("0")
        board2_price = self.board2.price if self.board2 else Decimal("0")
        addons_price = sum(addon.price for addon in self.addons.all()) if self.addons.exists() else Decimal("0")

        original_total = (base_price + board1_price + board2_price + addons_price) * quantity

        # Применяем скидку "Пицца недели" только для пицц размера "32"
        is_weekly_pizza = self.item.is_weekly_special and self.item_variant.size and self.item_variant.size.name == "32"
        
        discount_percent = Decimal("0")
        if is_weekly_pizza:
            # Получаем процент скидки из базы данных
            from app_home.models import Discount
            try:
                discount = Discount.objects.get(slug='picca-nedeli')
                discount_percent = Decimal(str(discount.percent)) / Decimal("100")
            except Discount.DoesNotExist:
                discount_percent = Decimal("0.2")  # 20% по умолчанию
        
        discount_amount = (base_price * quantity * discount_percent) if is_weekly_pizza else Decimal("0")

        final_total = original_total - discount_amount

        return {
            "original_total": original_total.quantize(Decimal(".01")),
            "final_total": final_total.quantize(Decimal(".01")),
            "discount_amount": discount_amount.quantize(Decimal(".01")),
            "is_weekly_pizza": is_weekly_pizza,
        }

    def is_available_in_branch(self, branch):
        """Проверяет, доступен ли товар в указанном филиале"""
        return self.item.category.branch.filter(id=branch.id).exists()

