"""Данные для дашборда руководителя: выручка, заказы, товары и категории.

Все показатели считаются из тех же заказов, что и остальная статистика:
оплаченные и не отменённые заказы за выбранный период. Период «неделя» —
последние 7 дней включая сегодня, «месяц» — последние 30 дней.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from app_order import statistics
from app_order.models import OrderItem

PERIODS = {
    "week": 7,
    "month": 30,
}
DEFAULT_PERIOD = "week"

# Девять самых продаваемых товаров и десятый сектор — все остальные.
TOP_PRODUCTS = 9

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
HOURS = list(range(24))


def resolve_period(period: str | None) -> str:
    """Приводит параметр периода к одному из поддерживаемых значений."""
    return period if period in PERIODS else DEFAULT_PERIOD


def period_bounds(period: str | None) -> tuple[str, date, date]:
    """Возвращает период и границы его дней включительно."""
    period = resolve_period(period)
    end = timezone.localdate()
    start = end - timedelta(days=PERIODS[period] - 1)
    return period, start, end


def _days_between(start: date, end: date) -> list[date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _revenue_series(orders, start: date, end: date) -> dict:
    """Выручка, количество заказов и средний чек по каждому дню периода."""
    revenue = defaultdict(lambda: Decimal("0.00"))
    counts = defaultdict(int)

    for order in orders:
        day = timezone.localtime(order.created_at).date()
        revenue[day] += order.total_price
        counts[day] += 1

    days = _days_between(start, end)
    labels = [day.strftime("%d.%m") for day in days]
    revenues = [_money(revenue[day]) for day in days]
    order_counts = [counts[day] for day in days]
    average_checks = [
        round(revenues[index] / order_counts[index], 2) if order_counts[index] else 0.0
        for index in range(len(days))
    ]

    return {
        "labels": labels,
        "revenue": revenues,
        "orders": order_counts,
        "average_check": average_checks,
    }


def _purchases_matrix(orders) -> dict:
    """Матрица 7×24: сколько заказов приходится на день недели и час."""
    matrix = [[0 for _ in HOURS] for _ in WEEKDAYS]

    for order in orders:
        local = timezone.localtime(order.created_at)
        matrix[local.isoweekday() - 1][local.hour] += 1

    return {
        "weekdays": WEEKDAYS,
        "hours": HOURS,
        "matrix": matrix,
        "max": max((count for row in matrix for count in row), default=0),
    }


def _products_share(orders) -> dict:
    """Топ-9 товаров по проданному количеству и сектор «Остальные»."""
    quantities = defaultdict(int)
    names = {}

    items = OrderItem.objects.filter(order__in=orders).select_related("product")
    for item in items:
        key = item.product_id
        quantities[key] += item.quantity
        names[key] = item.product.name

    ranked = sorted(quantities.items(), key=lambda pair: (-pair[1], names[pair[0]]))

    if len(ranked) > TOP_PRODUCTS:
        top = ranked[:TOP_PRODUCTS]
        rest = sum(quantity for _, quantity in ranked[TOP_PRODUCTS:])
        labels = [names[product_id] for product_id, _ in top] + ["Остальные"]
        values = [quantity for _, quantity in top] + [rest]
    else:
        labels = [names[product_id] for product_id, _ in ranked]
        values = [quantity for _, quantity in ranked]

    return {"labels": labels, "values": values}


def _categories_share(orders) -> dict:
    """Распределение проданного количества по категориям товаров."""
    quantities = defaultdict(int)

    items = OrderItem.objects.filter(order__in=orders).select_related("product__category")
    for item in items:
        quantities[item.product.category.name] += item.quantity

    ranked = sorted(quantities.items(), key=lambda pair: (-pair[1], pair[0]))

    return {
        "labels": [name for name, _ in ranked],
        "values": [quantity for _, quantity in ranked],
    }


def build_dashboard(period: str | None = None) -> dict:
    """Собирает все данные дашборда за выбранный период."""
    period, start, end = period_bounds(period)
    orders = list(statistics.get_orders(start, end))

    total_revenue = sum((order.total_price for order in orders), Decimal("0.00"))
    total_orders = len(orders)

    return {
        "period": period,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "start_label": start.strftime("%d.%m.%Y"),
        "end_label": end.strftime("%d.%m.%Y"),
        "summary": {
            "revenue": _money(total_revenue),
            "orders": total_orders,
            "average_check": (
                round(_money(total_revenue) / total_orders, 2) if total_orders else 0.0
            ),
        },
        "revenue": _revenue_series(orders, start, end),
        "purchases": _purchases_matrix(orders),
        "products": _products_share(orders),
        "categories": _categories_share(orders),
    }
