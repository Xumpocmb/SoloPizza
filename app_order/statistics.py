"""Расчёт статистики заказов в реальном времени по данным модели Order.

Статистика больше не хранится в БД: все отчёты (список дней, детализация по
филиалам, письма) собираются из заказов по требованию.
"""
from decimal import Decimal

from django.utils import timezone

from app_order.models import Order, OrderItem


STATUS_EXCLUDED = "canceled"


def get_orders(start_date=None, end_date=None):
    """Оплаченные неотменённые заказы за период (границы включительно)."""
    orders = Order.objects.filter(payment_status=True).exclude(status=STATUS_EXCLUDED)

    if start_date is not None:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date is not None:
        orders = orders.filter(created_at__date__lte=end_date)

    return orders


def _empty_branch(name):
    return {
        "name": name,
        "orders_count": 0,
        "total_cash": Decimal("0.00"),
        "total_card": Decimal("0.00"),
        "total_noname": Decimal("0.00"),
        "total_amount": Decimal("0.00"),
        "sold_items": {},
    }


def _add_order_payment(branch_data, order):
    """Распределяет сумму заказа по способам оплаты."""
    if order.payment_method == "split":
        branch_data["total_cash"] += order.cash_amount
        branch_data["total_card"] += order.card_amount
        branch_data["total_noname"] += order.noname_amount
    elif order.payment_method == "cash":
        branch_data["total_cash"] += order.total_price
    elif order.payment_method == "card":
        branch_data["total_card"] += order.total_price
    elif order.payment_method == "noname":
        branch_data["total_noname"] += order.total_price


def summarize_by_day(orders):
    """Сводка по каждому дню периода: количество заказов и суммы по оплатам."""
    days = {}

    for order in orders:
        day = timezone.localtime(order.created_at).date()
        if day not in days:
            days[day] = {
                "date": day,
                "orders_count": 0,
                "total_cash": Decimal("0.00"),
                "total_card": Decimal("0.00"),
                "total_noname": Decimal("0.00"),
                "total_amount": Decimal("0.00"),
                "sold_items": False,
            }

        days[day]["orders_count"] += 1
        _add_order_payment(days[day], order)

    for day in days.values():
        day["total_amount"] = day["total_cash"] + day["total_card"] + day["total_noname"]

    return sorted(days.values(), key=lambda day: day["date"], reverse=True)


def build_branch_statistics(orders):
    """Детальная статистика по филиалам за период, включая проданные товары."""
    branch_stats = {}

    for order in orders.select_related("branch"):
        branch = order.branch
        branch_id = branch.id if branch is not None else 0

        if branch_id not in branch_stats:
            branch_stats[branch_id] = _empty_branch(branch.name if branch is not None else "Без филиала")

        branch_stats[branch_id]["orders_count"] += 1
        _add_order_payment(branch_stats[branch_id], order)

    order_items = OrderItem.objects.filter(order__in=orders).select_related(
        "product", "variant", "order__branch"
    )

    for item in order_items:
        branch = item.order.branch
        branch_id = branch.id if branch is not None else 0
        branch_data = branch_stats.setdefault(
            branch_id, _empty_branch(branch.name if branch is not None else "Без филиала")
        )

        item_name = f"{item.product.name} ({item.get_size_display()})"
        item_data = branch_data["sold_items"].setdefault(item_name, {"quantity": 0, "payment_methods": {}})
        item_data["quantity"] += item.quantity

        item_final_total = item.calculate_item_total()["final_total"]
        order_payment_method = item.order.payment_method

        if order_payment_method == "split":
            total_order = item.order.total_price
            if total_order <= 0:
                continue

            split_shares = (
                ("Наличные (раздельно)", item.order.cash_amount),
                ("Карта (раздельно)", item.order.card_amount),
                ("Безналичный (раздельно)", item.order.noname_amount),
            )
            for method, amount in split_shares:
                share = item_final_total * (amount / total_order)
                item_data["payment_methods"][method] = item_data["payment_methods"].get(method, Decimal("0.00")) + share
        else:
            payment_method = item.order.get_payment_method_display()
            item_data["payment_methods"][payment_method] = item_data["payment_methods"].get(payment_method, Decimal("0.00")) + item_final_total

    for branch_data in branch_stats.values():
        branch_data["total_amount"] = (
            branch_data["total_cash"] + branch_data["total_card"] + branch_data["total_noname"]
        )

    return branch_stats