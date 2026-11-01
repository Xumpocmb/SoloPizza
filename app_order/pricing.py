"""Расчёт стоимости позиции (заказа и корзины).

Модуль не знает о моделях и БД: все входные данные передаются значениями,
чтобы формулу можно было вычислить для несохранённой позиции и проверить тестами.
"""

from decimal import Decimal


WEEKLY_PIZZA_SLUG = "weekly-pizza"
WEEKLY_PIZZA_NAME = "Пицца недели"
WEEKLY_PIZZA_DEFAULT_PERCENT = 20


def weekly_pizza_percent(percent_lookup):
    """Процент скидки «Пицца недели» из базы: по слагу, затем по названию, иначе 20 по умолчанию."""
    percent = percent_lookup(slug=WEEKLY_PIZZA_SLUG)
    if percent is None:
        percent = percent_lookup(name=WEEKLY_PIZZA_NAME)
    if percent is None:
        percent = WEEKLY_PIZZA_DEFAULT_PERCENT
    return Decimal(str(percent))


def resolve_discount(*, applies_pizza_discounts, delivery_type, is_partner,
                     partner_discount_percent, is_weekly_special, size_name, percent_lookup):
    """Скидка на базовую цену позиции заказа.

    Флаги независимы: при самовывозе пиццы недели размера "32" истинны и pickup, и weekly.
    """
    percent = Decimal("0")
    is_pickup = is_weekly = is_partner_discount = False

    if applies_pizza_discounts:
        # Если активирована скидка партнера, применяем только её
        if is_partner:
            # Используем значение процента скидки из заказа
            percent = Decimal(str(partner_discount_percent))
            is_partner_discount = True
        # Иначе применяем обычные скидки
        else:
            # Скидка на самовывоз
            if delivery_type == "pickup":
                # Получаем скидку "Самовывоз" из базы данных
                pickup_percent = percent_lookup(slug="pickup")
                if pickup_percent is None:
                    pickup_percent = percent_lookup(name="Самовывоз")
                if pickup_percent is not None:
                    percent = Decimal(str(pickup_percent))
                    is_pickup = True

                # Дополнительная скидка на пицца недели (только при самовывозе и только для размера "32")
                if is_weekly_special and size_name == "32":
                    percent = weekly_pizza_percent(percent_lookup)
                    is_weekly = True

    return {
        "discount_percent": percent,
        "is_pickup_discount": is_pickup,
        "is_weekly_pizza": is_weekly,
        "is_partner_discount": is_partner_discount,
    }


def calculate_line_total(*, base_price, quantity, board_prices, addon_prices, applies_pizza_discounts,
                         delivery_type, is_partner, partner_discount_percent, is_weekly_special,
                         size_name, percent_lookup):
    """Итог по позиции заказа: скидку разрешает resolve_discount, суммы считает line_totals."""
    discount = resolve_discount(
        applies_pizza_discounts=applies_pizza_discounts,
        delivery_type=delivery_type,
        is_partner=is_partner,
        partner_discount_percent=partner_discount_percent,
        is_weekly_special=is_weekly_special,
        size_name=size_name,
        percent_lookup=percent_lookup,
    )

    return line_totals(
        base_price=base_price,
        quantity=quantity,
        additions_price=sum(board_prices, Decimal("0")) + sum(addon_prices, Decimal("0")),
        discount_percent=discount["discount_percent"],
        is_pickup_discount=discount["is_pickup_discount"],
        is_weekly_pizza=discount["is_weekly_pizza"],
        is_partner_discount=discount["is_partner_discount"],
    )


def line_totals(*, base_price, quantity, additions_price, discount_percent,
                is_pickup_discount=False, is_weekly_pizza=False, is_partner_discount=False):
    """Суммы позиции по уже известному проценту скидки.

    Скидка берётся только с базовой цены: борты, добавки и другие дополнения
    всегда идут в итог полной стоимостью.
    """
    discount_amount = (base_price * (discount_percent / Decimal("100"))) * quantity
    original_total = (base_price + additions_price) * quantity
    discounted_base_price = base_price * (1 - discount_percent / Decimal("100"))
    final_total = (discounted_base_price * quantity) + additions_price * quantity

    return {
        "original_total": original_total.quantize(Decimal(".01")),
        "final_total": final_total.quantize(Decimal(".01")),
        "discount_amount": discount_amount.quantize(Decimal(".01")),
        "discount_percent": discount_percent,
        "is_weekly_pizza": is_weekly_pizza,
        "is_pickup_discount": is_pickup_discount,
        "is_partner_discount": is_partner_discount,
    }
