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


class PollNewOrdersTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.other_branch = CafeBranch.objects.create(name="Западный", address="ул. Мира, 2")
        self.url = reverse("app_order:poll_new_orders")

        self.staff = User.objects.create_user("pizzaiolo", password="pass", is_staff=True)
        self.customer = User.objects.create_user("client", password="pass")

    def _create_order(self, branch=None, customer_name="Иван", created_at=None, session_key=""):
        order = Order.objects.create(
            branch=branch or self.branch,
            customer_name=customer_name,
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method="cash",
            session_key=session_key,
        )
        if created_at is not None:
            # auto_now_add не даёт задать время вручную — обновляем отдельно
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order.refresh_from_db()
        return order

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_regular_user_forbidden(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_gets_empty_list_when_no_new_orders(self):
        self._create_order()
        self.client.force_login(self.staff)
        response = self.client.get(self.url, {"since": timezone.now().timestamp()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["orders"], [])

    def test_staff_sees_orders_created_after_since(self):
        self._create_order(customer_name="Старый", created_at=timezone.now() - timedelta(minutes=10))
        self._create_order(customer_name="Новый", created_at=timezone.now())

        self.client.force_login(self.staff)
        response = self.client.get(self.url, {"since": (timezone.now() - timedelta(minutes=1)).timestamp()})

        names = [order["customer_name"] for order in response.json()["orders"]]
        self.assertEqual(names, ["Новый"])
        self.assertIn("detail_url", response.json()["orders"][0])
        self.assertIn("number", response.json()["orders"][0])

    def test_orders_from_another_branch_are_ignored(self):
        self._create_order(branch=self.other_branch, created_at=timezone.now())
        self.client.force_login(self.staff)
        response = self.client.get(self.url, {"since": (timezone.now() - timedelta(minutes=1)).timestamp()})
        self.assertEqual(response.json()["orders"], [])

    def test_orders_from_same_session_are_ignored(self):
        self.client.force_login(self.staff)
        self.client.session["selected_branch_id"] = self.branch.id
        session_key = self.client.session.session_key

        self._create_order(session_key=session_key, created_at=timezone.now())

        response = self.client.get(self.url, {"since": (timezone.now() - timedelta(minutes=1)).timestamp()})
        self.assertEqual(response.json()["orders"], [])

    def test_invalid_since_does_not_break_request(self):
        self._create_order(created_at=timezone.now())
        self.client.force_login(self.staff)
        response = self.client.get(self.url, {"since": "не-число"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["orders"]), 1)

    def test_superuser_has_access(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", "pass")
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_order_list_page_embeds_poll_config(self):
        self.client.force_login(self.staff)
        self.client.session["selected_branch_id"] = self.branch.id

        response = self.client.get(reverse("app_order:order_list"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="order-poll-config"', content)
        # Метка времени обязана быть через точку, иначе ломается JS в ru-локали
        config = json.loads(re.search(r'id="order-poll-config"[^>]*>(.*?)</script>', content, re.DOTALL).group(1).replace("<", "\\u003c"))
        self.assertEqual(config["url"], reverse("app_order:poll_new_orders"))
        self.assertIsInstance(config["since"], float)

    def test_poll_script_not_rendered_for_regular_user(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("app_order:order_list"))
        self.assertNotContains(response, 'id="order-poll-config"')


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


class PrintCheckNumberTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", check_digit=3)
        self.staff = User.objects.create_user("pizzaiolo", password="pass", is_staff=True)
        self.client.force_login(self.staff)

    def _create_order(self):
        return Order.objects.create(
            branch=self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="pickup",
            payment_method="cash",
        )

    def test_all_items_check_shows_daily_number(self):
        # last_number=40 => первый заказ дня получает номер 41, а id у него будет небольшой:
        # так проверяем, что в чек попадает daily_number, а не старый id.
        DailyOrderNumber.objects.create(date=timezone.localdate(), last_number=40)
        order = self._create_order()

        response = self.client.get(reverse("app_order:print_non_fastfood_check", args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.print_number)
        self.assertContains(response, f"Заказ #:</strong> {order.print_number}")
        self.assertEqual(order.print_number, "3041")

    def test_fastfood_check_shows_daily_number(self):
        DailyOrderNumber.objects.create(date=timezone.localdate(), last_number=40)
        order = self._create_order()

        response = self.client.get(reverse("app_order:print_fastfood_check", args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Заказ #:</strong> {order.print_number}")
        self.assertEqual(order.print_number, "3041")


class StaffOrderListTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.staff = User.objects.create_user("pizzaiolo", password="pass", is_staff=True)
        self.client.force_login(self.staff)
        self.client.session["selected_branch_id"] = self.branch.id

    def _create_order(self, created_at=None):
        order = Order.objects.create(
            branch=self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method="cash",
        )
        if created_at is not None:
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order.refresh_from_db()
        return order

    def test_staff_sees_only_current_day_orders(self):
        self._create_order(created_at=timezone.now())
        self._create_order(created_at=timezone.now() - timedelta(days=1))
        self._create_order(created_at=timezone.now() - timedelta(days=5))

        response = self.client.get(reverse("app_order:order_list"))

        self.assertEqual(response.status_code, 200)
        orders = list(response.context["page_obj"].object_list)
        self.assertEqual(len(orders), 1)
        self.assertEqual(timezone.localtime(orders[0].created_at).date(), timezone.localdate())


class CustomerOrderListTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.customer = User.objects.create_user("client", password="pass")
        self.client.force_login(self.customer)
        self.client.session["selected_branch_id"] = self.branch.id

    def _create_order(self, user=None, guest_token="", session_key="", created_at=None):
        order = Order.objects.create(
            branch=self.branch,
            user=user,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method="cash",
            guest_token=guest_token,
            session_key=session_key,
        )
        if created_at is not None:
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order.refresh_from_db()
        return order

    def test_authenticated_user_sees_only_current_day_orders(self):
        self._create_order(user=self.customer, created_at=timezone.now())
        self._create_order(user=self.customer, created_at=timezone.now() - timedelta(days=1))

        response = self.client.get(reverse("app_order:order_list"))

        orders = list(response.context["page_obj"].object_list)
        self.assertEqual(len(orders), 1)
        self.assertEqual(timezone.localtime(orders[0].created_at).date(), timezone.localdate())

    def test_guest_sees_only_current_day_orders(self):
        self.client.logout()
        self.client.cookies["guest_token"] = "token-123"
        self.client.session["selected_branch_id"] = self.branch.id

        self._create_order(guest_token="token-123", created_at=timezone.now())
        self._create_order(guest_token="token-123", created_at=timezone.now() - timedelta(days=2))

        response = self.client.get(reverse("app_order:order_list"))

        orders = list(response.context["page_obj"].object_list)
        self.assertEqual(len(orders), 1)
        self.assertEqual(timezone.localtime(orders[0].created_at).date(), timezone.localdate())


class ReportsViewTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.staff = User.objects.create_user("stats", password="pass", is_staff=True)
        self.customer = User.objects.create_user("client", password="pass")

    def _create_order(self, total_price="0.00", payment_method="cash", created_at=None):
        order = Order.objects.create(
            branch=self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method=payment_method,
            total_price=total_price,
        )
        if created_at is not None:
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order.refresh_from_db()
        return order

    def test_regular_user_is_redirected(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("app_order:reports"))
        self.assertEqual(response.status_code, 302)

    def test_staff_has_access(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("app_order:reports")).status_code, 200)

    def test_superuser_has_access(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("app_order:reports")).status_code, 200)

    def test_shows_only_current_day(self):
        self._create_order(total_price="100.00", created_at=timezone.now())
        self._create_order(total_price="500.00", created_at=timezone.now() - timedelta(days=1))

        self.client.force_login(self.staff)
        response = self.client.get(reverse("app_order:reports"))

        self.assertEqual(response.context["total_orders_count"], 1)
        self.assertEqual(response.context["total_cash"], Decimal("100.00"))
        self.assertEqual(response.context["total_amount"], Decimal("100.00"))


class StatisticsTests(TestCase):
    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.other_branch = CafeBranch.objects.create(name="Западный", address="ул. Мира, 2")

        self.admin = User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.staff = User.objects.create_user("stats", password="pass", is_staff=True)
        self.customer = User.objects.create_user("client", password="pass")

    def _create_order(
        self,
        branch=None,
        total_price="0.00",
        payment_method="cash",
        payment_status=True,
        status="new",
        created_at=None,
        cash_amount="0.00",
        card_amount="0.00",
        noname_amount="0.00",
    ):
        order = Order.objects.create(
            branch=branch or self.branch,
            customer_name="Иван",
            phone_number="+375291112233",
            delivery_type="delivery",
            payment_method=payment_method,
            payment_status=payment_status,
            status=status,
            total_price=total_price,
            cash_amount=cash_amount,
            card_amount=card_amount,
            noname_amount=noname_amount,
        )
        if created_at is not None:
            Order.objects.filter(pk=order.pk).update(created_at=created_at)
            order.refresh_from_db()
        return order

    def test_get_orders_filters_unpaid_and_canceled(self):
        paid = self._create_order()
        self._create_order(payment_status=False)
        self._create_order(status="canceled")

        order_ids = set(statistics.get_orders().values_list("id", flat=True))
        self.assertEqual(order_ids, {paid.id})

    def test_get_orders_respects_date_bounds(self):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        old = self._create_order(created_at=timezone.now() - timedelta(days=1))
        recent = self._create_order(created_at=timezone.now())

        in_range = set(statistics.get_orders(today, today).values_list("id", flat=True))
        self.assertEqual(in_range, {recent.id})

        yesterday_only = set(statistics.get_orders(yesterday, yesterday).values_list("id", flat=True))
        self.assertEqual(yesterday_only, {old.id})

    def test_summarize_by_day_groups_and_totals(self):
        self._create_order(total_price="100.00", created_at=timezone.now())
        self._create_order(total_price="50.00", created_at=timezone.now())
        yesterday = timezone.now() - timedelta(days=1)
        self._create_order(total_price="70.00", created_at=yesterday)

        summary = statistics.summarize_by_day(statistics.get_orders())
        by_date = {row["date"]: row for row in summary}

        today = timezone.localdate()
        self.assertEqual(by_date[today]["orders_count"], 2)
        self.assertEqual(by_date[today]["total_cash"], Decimal("150.00"))
        self.assertEqual(by_date[today]["total_amount"], Decimal("150.00"))

        old_day = (today - timedelta(days=1))
        self.assertEqual(by_date[old_day]["orders_count"], 1)
        self.assertEqual(by_date[old_day]["total_cash"], Decimal("70.00"))

    def test_summarize_by_day_sorts_newest_first(self):
        self._create_order(created_at=timezone.now())
        self._create_order(created_at=timezone.now() - timedelta(days=2))

        dates = [row["date"] for row in statistics.summarize_by_day(statistics.get_orders())]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_summarize_by_day_uses_local_date(self):
        self._create_order(created_at=timezone.now())
        row = statistics.summarize_by_day(statistics.get_orders())[0]
        self.assertEqual(row["date"], timezone.localdate())

    def test_build_branch_statistics_groups_by_branch(self):
        self._create_order(branch=self.branch, total_price="100.00")
        self._create_order(branch=self.branch, total_price="20.00", payment_method="card")
        self._create_order(branch=self.other_branch, total_price="30.00", payment_method="noname")

        stats = statistics.build_branch_statistics(statistics.get_orders())

        self.assertEqual(stats[self.branch.id]["orders_count"], 2)
        self.assertEqual(stats[self.branch.id]["total_cash"], Decimal("100.00"))
        self.assertEqual(stats[self.branch.id]["total_card"], Decimal("20.00"))
        self.assertEqual(stats[self.branch.id]["total_amount"], Decimal("120.00"))

        self.assertEqual(stats[self.other_branch.id]["orders_count"], 1)
        self.assertEqual(stats[self.other_branch.id]["total_noname"], Decimal("30.00"))

    def test_build_branch_statistics_splits_payment(self):
        self._create_order(
            payment_method="split",
            total_price="100.00",
            cash_amount="40.00",
            card_amount="60.00",
        )
        stats = statistics.build_branch_statistics(statistics.get_orders())
        branch = stats[self.branch.id]
        self.assertEqual(stats[self.branch.id]["total_cash"], Decimal("40.00"))
        self.assertEqual(stats[self.branch.id]["total_card"], Decimal("60.00"))

    def test_build_branch_statistics_collects_sold_items(self):
        category = Category.objects.create(name="Напитки", slug="drinks")
        product = Product.objects.create(name="Кола", slug="cola", category=category)
        variant = ProductVariant.objects.create(product=product, value="0.5", unit="l", price="80.00")

        order = self._create_order(total_price="160.00")
        OrderItem.objects.create(order=order, product=product, variant=variant, quantity=2)

        stats = statistics.build_branch_statistics(statistics.get_orders())
        sold = stats[self.branch.id]["sold_items"]

        self.assertIn("Кола (0.5 л)", sold)
        self.assertEqual(sold["Кола (0.5 л)"]["quantity"], 2)
        self.assertEqual(sold["Кола (0.5 л)"]["payment_methods"]["Наличные"], Decimal("160.00"))

    def test_order_statistics_view_requires_superuser(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("app_order:order_statistics")).status_code, 403)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("app_order:order_statistics")).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("app_order:order_statistics")).status_code, 200)

    def test_order_statistics_view_renders_live_rows(self):
        self._create_order(total_price="100.00")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("app_order:order_statistics"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"].object_list), 1)
        self.assertEqual(response.context["page_obj"].object_list[0]["total_amount"], Decimal("100.00"))

    def test_order_statistics_view_ignores_invalid_sort(self):
        self._create_order()
        self.client.force_login(self.admin)

        response = self.client.get(reverse("app_order:order_statistics"), {"sort": "hack"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort_by"], "date")

    def test_detail_statistics_view_computes_live(self):
        self._create_order(total_price="100.00")
        self.client.force_login(self.admin)
        today = timezone.localdate().isoformat()

        response = self.client.get(reverse("app_order:detail_statistics", args=[today]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["branch_statistics"][self.branch.id]["total_amount"], Decimal("100.00"))

    def test_detail_statistics_view_rejects_bad_date(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("app_order:detail_statistics", args=["not-a-date"]))
        self.assertEqual(response.status_code, 404)