import json
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from app_home.models import CafeBranch, SiteSettings, WorkingHours
from app_catalog.models import Category, PizzaSizes, Product, ProductVariant
from app_order import statistics
from app_order.models import DailyOrderNumber, Order, OrderItem
from app_order.forms import CheckoutForm, OrderEditForm
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


class OrderFormValidationTests(TestCase):
    """Общие правила адреса/телефона и проверка раздельной оплаты при правке заказа."""

    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", check_digit=7)
        self.size = PizzaSizes.objects.create(name="32")
        self.category = Category.objects.create(name="Пицца", slug="pizza", applies_pizza_discounts=True)
        self.product = Product.objects.create(name="Пепперони", slug="pepperoni", category=self.category)
        self.variant = ProductVariant.objects.create(product=self.product, size=self.size, price=Decimal("25.00"))
        self.order = Order.objects.create(
            branch=self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="pickup",
            payment_method="cash",
        )
        # Сумма заказа считается из позиций: 25.00 × 2 = 50.00, пересчёт идёт в сигнале OrderItem
        OrderItem.objects.create(order=self.order, product=self.product, variant=self.variant, quantity=2)

    def edit_data(self, **overrides):
        data = {
            "customer_name": "Иван",
            "phone_number": "+375291112233",
            "delivery_type": "pickup",
            "payment_method": "split",
            "partner_discount_percent": 10,
            "cash_amount": "30.00",
            "card_amount": "20.00",
            "noname_amount": "0.00",
        }
        data.update(overrides)
        return data

    def test_split_payment_matching_total_is_accepted(self):
        form = OrderEditForm(self.edit_data(), instance=self.order)
        self.assertTrue(form.is_valid(), form.errors)

    def test_split_payment_mismatch_is_rejected(self):
        form = OrderEditForm(self.edit_data(card_amount="10.00"), instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn("Сумма раздельной оплаты", form.non_field_errors()[0])

    def test_split_checked_against_new_total_after_partner_toggle(self):
        """Флажок партнёра меняет итог (50.00 → 40.00 при скидке 20%): суммы сверяются с новым итогом."""
        form = OrderEditForm(self.edit_data(is_partner="on", partner_discount_percent=20), instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn("Сумма раздельной оплаты", form.non_field_errors()[0])

        form = OrderEditForm(
            self.edit_data(is_partner="on", partner_discount_percent=20, cash_amount="25.00", card_amount="15.00"),
            instance=self.order,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_difference_of_one_kopeyka_is_rejected(self):
        """При двух знаках после запятой допуск 0.01 означает фактическое требование точного совпадения."""
        form = OrderEditForm(self.edit_data(card_amount="19.99"), instance=self.order)
        self.assertFalse(form.is_valid())

    def test_split_mismatch_does_not_hide_other_errors(self):
        form = OrderEditForm(self.edit_data(card_amount="10.00", delivery_type="delivery", address=""), instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn("address", form.errors)
        self.assertIn("Сумма раздельной оплаты", form.non_field_errors()[0])

    def test_pickup_fills_address_placeholder(self):
        form = OrderEditForm(self.edit_data(payment_method="cash", address=""), instance=self.order)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["address"], "Самовывоз")

    def test_delivery_requires_address(self):
        form = OrderEditForm(self.edit_data(payment_method="cash", delivery_type="delivery", address=""), instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn("address", form.errors)

    def test_hall_allows_empty_phone(self):
        form = OrderEditForm(self.edit_data(payment_method="cash", delivery_type="cafe", phone_number=""), instance=self.order)
        self.assertTrue(form.is_valid(), form.errors)

    def test_checkout_form_uses_the_same_rules(self):
        form = CheckoutForm({"customer_name": "Иван", "phone_number": "", "delivery_type": "cafe", "payment_method": "cash"})
        self.assertTrue(form.is_valid(), form.errors)

        form = CheckoutForm({"customer_name": "Иван", "phone_number": "", "delivery_type": "delivery", "payment_method": "cash"})
        self.assertFalse(form.is_valid())
        self.assertIn("address", form.errors)
        self.assertIn("phone_number", form.errors)



class CheckoutWorkingHoursTests(TestCase):
    """Оформление заказа учитывает график филиала и отсечку за 30 минут."""

    THURSDAY = date(2026, 11, 5)

    def setUp(self):
        self.client = Client()
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", check_digit=7)
        self.category = Category.objects.create(name="Пицца", slug="pizza")
        self.category.branch.add(self.branch)
        self.size = PizzaSizes.objects.create(name="32")
        self.product = Product.objects.create(name="Пепперони", slug="pepperoni", category=self.category)
        self.variant = ProductVariant.objects.create(product=self.product, size=self.size, price=Decimal("25.00"))
        self.working_hours = WorkingHours.objects.create(
            branch=self.branch,
            day_of_week=self.THURSDAY.isoweekday(),
            opening_time=time(11),
            closing_time=time(23),
        )

        session = self.client.session
        session["selected_branch_id"] = str(self.branch.id)
        session["cart"] = {
            f"{self.product.id}-{self.variant.id}": {
                "product_id": self.product.id,
                "variant_id": self.variant.id,
                "quantity": 1,
                "board1_id": None,
                "board2_id": None,
                "sauce_id": None,
                "addons_ids": [],
                "drink": None,
            }
        }
        session.save()

    def at(self, hour, minute=0):
        return timezone.make_aware(datetime.combine(self.THURSDAY, time(hour, minute)))

    def get_checkout(self, hour, minute=0):
        with patch("app_home.working_hours._now", return_value=self.at(hour, minute)):
            return self.client.get(reverse("app_order:checkout"), follow=True)

    def test_user_can_checkout_before_cutoff(self):
        response = self.get_checkout(22, 29)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_order/checkout.html")

    def test_user_cannot_checkout_thirty_minutes_before_closing(self):
        response = self.get_checkout(22, 30)

        self.assertRedirects(response, reverse("app_cart:view_cart"))
        self.assertContains(response, "Приём заказов прекращается за 30 минут")

    def test_staff_can_checkout_outside_working_hours(self):
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        self.client.force_login(staff)

        response = self.get_checkout(23, 30)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_order/checkout.html")

    def test_superuser_can_checkout_when_branch_is_closed(self):
        self.working_hours.is_closed = True
        self.working_hours.save()
        admin = User.objects.create_superuser(username="admin", password="Sup3r-secret")
        self.client.force_login(admin)

        response = self.get_checkout(12, 0)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_order/checkout.html")

    def test_staff_can_checkout_when_site_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        self.client.force_login(staff)

        response = self.get_checkout(12, 0)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_order/checkout.html")

    def test_regular_user_is_blocked_when_site_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()

        response = self.get_checkout(12, 0)

        self.assertRedirects(response, reverse("app_cart:view_cart"))
        self.assertContains(response, "В настоящий момент оформление новых заказов недоступно")
