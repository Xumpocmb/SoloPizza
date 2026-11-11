import uuid
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from app_api.auth import issue_tokens
from app_catalog.models import BoardParams, Category, PizzaBoard, PizzaSauce, PizzaSizes, Product, ProductVariant
from app_home.models import CafeBranch, Discount, SiteSettings
from app_order.models import Order

User = get_user_model()


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
@mock.patch("app_api.orders.is_order_time_allowed", return_value=True)  # график филиала покрыт тестами app_home
class OrderApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.branch = CafeBranch.objects.create(name="Ленина", address="ул. Ленина 9/1", is_active=True)
        pizza_cat = Category.objects.create(name="Пицца", slug="pizza", applies_pizza_discounts=True)
        pizza_cat.branch.add(self.branch)
        Discount.objects.create(name="Самовывоз", slug="pickup", percent=10)
        Discount.objects.create(name="Пицца недели", slug="weekly-pizza", percent=20)

        self.size_25 = PizzaSizes.objects.create(name="25")
        self.size_32 = PizzaSizes.objects.create(name="32")
        self.sauce = PizzaSauce.objects.create(name="Итальянский")
        self.pizza = Product.objects.create(
            name="Ассорти", slug="assorti", category=pizza_cat, has_base_sauce=True, has_border=True
        )
        self.pizza_25 = ProductVariant.objects.create(product=self.pizza, size=self.size_25, price=Decimal("13.50"))
        self.board_25 = BoardParams.objects.create(
            board=PizzaBoard.objects.create(name="Чеддер"), size=self.size_25, price=Decimal("2.50")
        )
        self.weekly = Product.objects.create(
            name="Челентано", slug="chelentano", category=pizza_cat, has_base_sauce=True, is_weekly_special=True
        )
        self.weekly_32 = ProductVariant.objects.create(product=self.weekly, size=self.size_32, price=Decimal("21.50"))

        self.user = User.objects.create_user(username="ivan", email="ivan@gmail.com")
        self.client = self.client_for(self.user)
        self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json")

    def client_for(self, user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
        return client

    def add_pizza(self, **extra):
        payload = {"product_id": self.pizza.pk, "variant_id": self.pizza_25.pk, "sauce_id": self.sauce.pk, **extra}
        response = self.client.post("/api/v1/cart/items/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.json())

    def order_payload(self, **extra):
        return {
            "client_order_id": str(uuid.uuid4()), "delivery_type": "pickup", "payment_method": "cash",
            "customer_name": "Иван", "phone": "+375 (29) 111-22-33", "consent": True, **extra,
        }

    def test_options_offer_only_app_choices(self, _):
        data = self.client.get("/api/v1/checkout/options/").json()
        self.assertEqual([d["id"] for d in data["delivery_types"]], ["pickup", "delivery"])
        self.assertEqual([p["id"] for p in data["payment_methods"]], ["cash", "card"])
        self.assertTrue(data["available"])

    def test_quote_matches_site_rules_for_pickup_and_delivery(self, _):
        self.add_pizza(board1_id=self.board_25.pk)  # 13.50 + борт 2.50
        pickup = self.client.post("/api/v1/checkout/quote/", {"delivery_type": "pickup"}, format="json").json()
        # скидка самовывоза 10% — только с базовой цены, борт полной стоимостью
        self.assertEqual((pickup["discount_amount"], pickup["delivery_cost"], pickup["total_price"]), ("1.35", "0.00", "14.65"))
        delivery = self.client.post("/api/v1/checkout/quote/", {"delivery_type": "delivery"}, format="json").json()
        # без скидки; доставка 3.00, пока сумма меньше 20
        self.assertEqual((delivery["discount_amount"], delivery["delivery_cost"], delivery["total_price"]), ("0.00", "3.00", "19.00"))

    def test_weekly_pizza_32_gets_its_discount_on_pickup(self, _):
        self.client.post(
            "/api/v1/cart/items/",
            {"product_id": self.weekly.pk, "variant_id": self.weekly_32.pk, "sauce_id": self.sauce.pk},
            format="json",
        )
        quote = self.client.post("/api/v1/checkout/quote/", {"delivery_type": "pickup"}, format="json").json()
        self.assertEqual((quote["discount_amount"], quote["total_price"]), ("4.30", "17.20"))  # 20% от 21.50

    def test_order_is_created_from_cart_with_server_prices_only(self, _):
        self.add_pizza(board1_id=self.board_25.pk)
        quote = self.client.post("/api/v1/checkout/quote/", {"delivery_type": "pickup"}, format="json").json()
        response = self.client.post("/api/v1/orders/", self.order_payload(
            # всё это клиент не задаёт — сервер игнорирует
            is_partner=True, partner_discount_percent=100, total_price="0.01", status="completed", payment_status=True,
        ), format="json")
        self.assertEqual(response.status_code, 201, response.json())
        data = response.json()
        self.assertEqual((data["total_price"], data["status"]), (quote["total_price"], "new"))
        order = Order.objects.get(pk=data["id"])
        self.assertEqual((order.source, order.user, order.branch, order.is_partner, order.payment_status),
                         ("app", self.user, self.branch, False, False))
        self.assertEqual(order.phone_number, "+375291112233")
        self.assertIsNotNone(order.consent_at)
        self.assertEqual(self.client.get("/api/v1/cart/").json()["items"], [])

    def test_repeated_submit_returns_the_same_order(self, _):
        self.add_pizza()
        payload = self.order_payload()
        first = self.client.post("/api/v1/orders/", payload, format="json")
        second = self.client.post("/api/v1/orders/", payload, format="json")
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(Order.objects.count(), 1)

    def test_consent_address_and_empty_cart_are_checked(self, _):
        self.assertIn("cart", self.client.post("/api/v1/orders/", self.order_payload(), format="json").json())
        self.add_pizza()
        self.assertIn("consent", self.client.post("/api/v1/orders/", self.order_payload(consent=False), format="json").json())
        no_address = self.client.post("/api/v1/orders/", self.order_payload(delivery_type="delivery"), format="json")
        self.assertIn("address", no_address.json())
        self.assertEqual(Order.objects.count(), 0)

    def test_closed_branch_or_disabled_orders_are_refused(self, time_allowed):
        self.add_pizza()
        time_allowed.return_value = False
        closed = self.client.post("/api/v1/orders/", self.order_payload(), format="json")
        self.assertEqual(closed.status_code, 400)
        self.assertFalse(self.client.get("/api/v1/checkout/options/").json()["available"])
        time_allowed.return_value = True
        SiteSettings.objects.update_or_create(pk=1, defaults={"orders_available": False})
        self.assertEqual(self.client.post("/api/v1/orders/", self.order_payload(), format="json").status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_product_hidden_after_adding_blocks_order(self, _):
        self.add_pizza()
        Product.objects.filter(pk=self.pizza.pk).update(is_active=False)
        response = self.client.post("/api/v1/orders/", self.order_payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Ассорти", response.json()["cart"])

    def test_user_sees_only_own_orders_including_site_ones(self, _):
        site_order = Order.objects.create(
            user=self.user, branch=self.branch, customer_name="Иван", phone_number="+375291112233",
            delivery_type="pickup", payment_method="cash",
        )
        stranger = User.objects.create_user(username="petr")
        foreign = Order.objects.create(
            user=stranger, branch=self.branch, customer_name="Пётр", phone_number="+375291112244",
            delivery_type="pickup", payment_method="cash",
        )
        self.assertEqual([o["id"] for o in self.client.get("/api/v1/orders/").json()], [site_order.pk])
        self.assertEqual(self.client.get(f"/api/v1/orders/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/orders/{site_order.pk}/").json()["number"], site_order.print_number)

    def test_requires_login(self, _):
        anonymous = APIClient()
        self.assertEqual(anonymous.get("/api/v1/orders/").status_code, 401)
        self.assertEqual(anonymous.post("/api/v1/checkout/quote/", {"delivery_type": "pickup"}, format="json").status_code, 401)
