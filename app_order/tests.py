import json
import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app_home.models import CafeBranch
from app_order.models import DailyOrderNumber, Order


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