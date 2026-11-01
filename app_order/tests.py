import json
import re
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app_home.models import CafeBranch
from app_catalog.models import Category, Product, ProductVariant
from app_order import statistics
from app_order.models import DailyOrderNumber, Order, OrderItem


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

