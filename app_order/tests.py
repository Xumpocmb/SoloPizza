import json
import re
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from app_home.models import CafeBranch
from app_catalog.models import Category, Product, ProductVariant
from app_order import statistics
from app_order.models import DailyOrderNumber, Order, OrderItem
from app_order.pricing import calculate_line_total, line_totals


class DailyNumberingTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", check_digit=7)

    def _create_order(self):
        return Order.objects.create(
            branch=self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method="cash",
        )

    def test_first_order_of_day_gets_number_one(self):
        order = self._create_order()
        self.assertEqual(order.daily_number, 1)
        self.assertEqual(order.number_date, timezone.localdate())
        self.assertEqual(order.print_number, "7001")

    def test_numbers_increment_within_day(self):
        first = self._create_order()
        second = self._create_order()
        self.assertEqual((first.daily_number, second.daily_number), (1, 2))
        self.assertEqual(second.print_number, "7002")

    def test_canceled_order_keeps_its_number(self):
        canceled = self._create_order()
        canceled.status = "canceled"
        canceled.save()

        following = self._create_order()

        self.assertEqual(canceled.daily_number, 1)
        self.assertEqual(following.daily_number, 2)

    def test_numbering_resets_next_day(self):
        today_order = self._create_order()
        tomorrow = timezone.localdate() + timedelta(days=1)

        with patch("app_order.models.timezone.localdate", return_value=tomorrow):
            tomorrow_order = self._create_order()

        self.assertEqual(today_order.daily_number, 1)
        self.assertEqual(tomorrow_order.daily_number, 1)
        self.assertEqual(tomorrow_order.number_date, tomorrow)

    def test_branch_change_keeps_daily_number_and_changes_prefix(self):
        order = self._create_order()
        other = CafeBranch.objects.create(name="Западный", address="ул. Мира, 2", check_digit=3)

        order.branch = other
        order.save()

        self.assertEqual(order.daily_number, 1)
        self.assertEqual(order.print_number, "3001")

    def test_duplicate_number_in_day_is_rejected(self):
        first = self._create_order()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(
                    branch=self.branch,
                    customer_name="Пётр",
                    phone_number="+375291112233",
                    delivery_type="delivery",
                    payment_method="cash",
                    daily_number=first.daily_number,
                    number_date=first.number_date,
                )


class PricingTests(SimpleTestCase):
    """Расчёт позиции без БД: чистая функция получает все данные аргументами."""

    @staticmethod
    def lookup(**percents):
        def percent_lookup(slug=None, name=None):
            return percents.get(slug or name)

        return percent_lookup

    @staticmethod
    def line(**overrides):
        params = {
            "base_price": Decimal("30.00"),
            "quantity": 1,
            "board_prices": [],
            "addon_prices": [],
            "applies_pizza_discounts": True,
            "delivery_type": "delivery",
            "is_partner": False,
            "partner_discount_percent": Decimal("0"),
            "is_weekly_special": False,
            "size_name": None,
            "percent_lookup": PricingTests.lookup(pickup=10, **{"weekly-pizza": 20}),
        }
        params.update(overrides)
        return calculate_line_total(**params)

    def test_no_discount_when_category_excluded(self):
        calculation = self.line(
            applies_pizza_discounts=False,
            delivery_type="pickup",
            is_weekly_special=True,
            size_name="32",
        )
        self.assertEqual(calculation["discount_percent"], Decimal("0"))
        self.assertEqual(calculation["final_total"], Decimal("30.00"))
        self.assertEqual(calculation["discount_amount"], Decimal("0.00"))

    def test_boards_and_addons_are_not_discounted(self):
        calculation = self.line(
            quantity=2,
            board_prices=[Decimal("5.00")],
            addon_prices=[Decimal("3.00"), Decimal("2.00")],
            delivery_type="pickup",
        )
        # Скидка 10% только с базы 30.00 * 2, борты и добавки идут полной суммой
        self.assertEqual(calculation["original_total"], Decimal("80.00"))
        self.assertEqual(calculation["discount_amount"], Decimal("6.00"))
        self.assertEqual(calculation["final_total"], Decimal("74.00"))

    def test_pickup_discount_by_slug(self):
        calculation = self.line(delivery_type="pickup")
        self.assertEqual(calculation["discount_percent"], Decimal("10"))
        self.assertTrue(calculation["is_pickup_discount"])
        self.assertFalse(calculation["is_weekly_pizza"])

    def test_pickup_discount_by_name_when_slug_missing(self):
        calculation = self.line(
            delivery_type="pickup",
            percent_lookup=self.lookup(**{"Самовывоз": 7}),
        )
        self.assertEqual(calculation["discount_percent"], Decimal("7"))
        self.assertTrue(calculation["is_pickup_discount"])

    def test_weekly_pizza_32_replaces_amount_and_keeps_pickup_flag(self):
        calculation = self.line(delivery_type="pickup", is_weekly_special=True, size_name="32")
        self.assertTrue(calculation["is_pickup_discount"])
        self.assertTrue(calculation["is_weekly_pizza"])
        self.assertEqual(calculation["discount_percent"], Decimal("20"))

    def test_weekly_pizza_other_size_keeps_pickup_only(self):
        calculation = self.line(delivery_type="pickup", is_weekly_special=True, size_name="26")
        self.assertTrue(calculation["is_pickup_discount"])
        self.assertFalse(calculation["is_weekly_pizza"])
        self.assertEqual(calculation["discount_percent"], Decimal("10"))

    def test_weekly_pizza_default_twenty_when_no_discount_rows(self):
        calculation = self.line(
            delivery_type="pickup",
            is_weekly_special=True,
            size_name="32",
            percent_lookup=self.lookup(),
        )
        self.assertEqual(calculation["discount_percent"], Decimal("20"))

    def test_weekly_pizza_needs_pickup(self):
        calculation = self.line(delivery_type="delivery", is_weekly_special=True, size_name="32")
        self.assertEqual(calculation["discount_percent"], Decimal("0"))
        self.assertFalse(calculation["is_weekly_pizza"])

    def test_partner_discount_wins_over_pickup_and_weekly(self):
        calculation = self.line(
            delivery_type="pickup",
            is_weekly_special=True,
            size_name="32",
            is_partner=True,
            partner_discount_percent=Decimal("15.5"),
        )
        self.assertTrue(calculation["is_partner_discount"])
        self.assertFalse(calculation["is_pickup_discount"])
        self.assertFalse(calculation["is_weekly_pizza"])
        self.assertEqual(calculation["discount_amount"], Decimal("4.65"))
        self.assertEqual(calculation["final_total"], Decimal("25.35"))

    def test_quantity_multiplies_everything(self):
        calculation = self.line(quantity=3, addon_prices=[Decimal("4.00")], delivery_type="pickup")
        self.assertEqual(calculation["original_total"], Decimal("102.00"))
        self.assertEqual(calculation["final_total"], Decimal("93.00"))


class LineTotalsTests(SimpleTestCase):
    """Общая арифметика позиции — её считают и заказ, и корзина."""

    @staticmethod
    def totals(**overrides):
        params = {
            "base_price": Decimal("30.00"),
            "quantity": 1,
            "additions_price": Decimal("0"),
            "discount_percent": Decimal("0"),
        }
        params.update(overrides)
        return line_totals(**params)

    def test_without_discount(self):
        calculation = self.totals(base_price=Decimal("25.05"), quantity=2, additions_price=Decimal("42.50"))
        self.assertEqual(calculation["original_total"], Decimal("135.10"))
        self.assertEqual(calculation["final_total"], Decimal("135.10"))
        self.assertEqual(calculation["discount_amount"], Decimal("0.00"))

    def test_discount_touches_only_base_price(self):
        calculation = self.totals(additions_price=Decimal("10.00"), discount_percent=Decimal("20"))
        self.assertEqual(calculation["original_total"], Decimal("40.00"))
        self.assertEqual(calculation["discount_amount"], Decimal("6.00"))
        self.assertEqual(calculation["final_total"], Decimal("34.00"))

    def test_rounded_values_stay_consistent(self):
        calculation = self.totals(base_price=Decimal("199.99"), quantity=3, discount_percent=Decimal("15"))
        self.assertEqual(calculation["original_total"], Decimal("599.97"))
        self.assertEqual(calculation["discount_amount"], Decimal("90.00"))
        self.assertEqual(calculation["final_total"], Decimal("509.97"))
        self.assertEqual(
            calculation["final_total"],
            calculation["original_total"] - calculation["discount_amount"],
        )

    def test_flags_are_passed_through(self):
        calculation = self.totals(discount_percent=Decimal("20"), is_weekly_pizza=True, is_pickup_discount=True)
        self.assertTrue(calculation["is_weekly_pizza"])
        self.assertTrue(calculation["is_pickup_discount"])
        self.assertFalse(calculation["is_partner_discount"])

