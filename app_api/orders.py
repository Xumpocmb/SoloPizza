"""Оформление заказа из корзины приложения.

Суммы считаются теми же функциями, что и заказы сайта: calculate_line_total из
app_order.pricing (скидки самовывоза и «Пиццы недели») и OrderManager._calculate_delivery_cost
(доставка). Партнёрская скидка — только у сотрудников на сайте, приложению недоступна.
"""

from decimal import Decimal
from types import SimpleNamespace

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from app_api.filters import catalog_products
from app_home.models import SiteSettings
from app_home.working_hours import is_order_time_allowed, order_time_restriction_message
from app_order.models import DiscountCache, Order, OrderItem, suspended_order_totals
from app_order.pricing import calculate_line_total

DELIVERY_TYPES = ("pickup", "delivery")  # «Зал» — только для сотрудников
PAYMENT_METHODS = ("cash", "card")  # оплата при получении; безнал и раздельная — у сотрудников


def availability(cart, user):
    """(можно ли оформить сейчас, причина) — те же проверки, что у checkout сайта."""
    if not SiteSettings.is_orders_available(user):
        return False, "В настоящий момент оформление новых заказов недоступно."
    if not is_order_time_allowed(cart.branch, user):
        return False, order_time_restriction_message(cart.branch)
    return True, ""


def _cart_items(cart):
    return list(
        cart.items.select_related("item__category", "item_variant__size", "board1", "board2", "sauce").prefetch_related("addons")
    )


def quote(cart, delivery_type):
    """Итог корзины для способа получения: позиции со скидками, доставка, total."""
    discounts = DiscountCache()
    lines = []
    for item in _cart_items(cart):
        calculation = calculate_line_total(
            base_price=item.item_variant.price,
            quantity=item.quantity,
            board_prices=[board.price for board in (item.board1, item.board2) if board is not None],
            addon_prices=[addon.price for addon in item.addons.all()],
            applies_pizza_discounts=item.item.category.applies_pizza_discounts,
            delivery_type=delivery_type,
            is_partner=False,
            partner_discount_percent=0,
            is_weekly_special=item.item.is_weekly_special,
            size_name=item.item_variant.size.name if item.item_variant.size else None,
            percent_lookup=discounts.percent,
        )
        lines.append((item, calculation))

    subtotal = sum((c["original_total"] for _, c in lines), Decimal("0.00"))
    discount = sum((c["discount_amount"] for _, c in lines), Decimal("0.00"))
    # тот же метод, что считает доставку заказам сайта; ему нужны только product и итоги позиций
    delivery_cost = Order.objects._calculate_delivery_cost(
        Order(delivery_type=delivery_type), [(SimpleNamespace(product=item.item), c) for item, c in lines]
    )
    return {
        "lines": lines,
        "subtotal": subtotal,
        "discount_amount": discount,
        "delivery_cost": delivery_cost,
        "total_price": subtotal - discount + delivery_cost,
    }


def create_order(user, cart, data):
    """Заказ из корзины пользователя. Повтор с тем же client_order_id возвращает уже созданный заказ."""
    existing = Order.objects.filter(user=user, client_order_id=data["client_order_id"]).first()
    if existing is not None:
        return existing, False

    items = _cart_items(cart)
    if not items:
        raise ValidationError({"cart": "Корзина пуста"})
    allowed, reason = availability(cart, user)
    if not allowed:
        raise ValidationError({"detail": reason})
    available = set(catalog_products(cart.branch_id).values_list("pk", flat=True))
    unavailable = sorted({item.item.name for item in items if item.item_id not in available})
    if unavailable:
        raise ValidationError({"cart": f"Недоступно в филиале «{cart.branch.name}»: {', '.join(unavailable)}"})

    try:
        return _create(user, cart, items, data), True
    except IntegrityError:
        # параллельный повтор с тем же client_order_id успел создать заказ первым
        existing = Order.objects.filter(user=user, client_order_id=data["client_order_id"]).first()
        if existing is None:
            raise
        return existing, False


def _create(user, cart, items, data):
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            branch=cart.branch,
            source="app",
            client_order_id=data["client_order_id"],
            consent_at=timezone.now(),
            customer_name=data["customer_name"],
            phone_number=data["phone"],
            address=data.get("address") or None,
            delivery_type=data["delivery_type"],
            payment_method=data["payment_method"],
            comment=data.get("comment", ""),
            status="new",
            payment_status=False,
        )
        with suspended_order_totals():
            for item in items:
                order_item = OrderItem.objects.create(
                    order=order, product=item.item, variant=item.item_variant, quantity=item.quantity,
                    board1=item.board1, board2=item.board2, sauce=item.sauce, drink=item.drink,
                )
                addons = list(item.addons.all())
                if addons:
                    order_item.addons.set(addons)
        order.recalculate_totals()
        cart.items.all().delete()
        cart.touch()
    return order
