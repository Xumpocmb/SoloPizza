import uuid
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from app_catalog.models import (
    AddonParams,
    BoardParams,
    Category,
    ComboDrinks,
    PizzaAddon,
    PizzaBoard,
    PizzaSauce,
    PizzaSizes,
    Product,
    ProductVariant,
)
from app_home.models import CafeBranch


# Троттлинг корзины пишет счётчики в кэш — в проде Redis, в тестах локальная память.
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class CartApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.branch = CafeBranch.objects.create(name="Ленина", address="ул. Ленина 9/1", is_active=True)
        self.other_branch = CafeBranch.objects.create(name="Тексер", address="ул. Тексер, 4а", is_active=True)

        pizza_cat = Category.objects.create(name="Пицца", slug="pizza")
        pizza_cat.branch.add(self.branch)
        combo_cat = Category.objects.create(name="Комбо", slug="combo")
        combo_cat.branch.add(self.branch)

        self.size_25 = PizzaSizes.objects.create(name="25")
        self.size_32 = PizzaSizes.objects.create(name="32")
        self.pizza = Product.objects.create(
            name="Ассорти", slug="assorti", category=pizza_cat,
            has_base_sauce=True, has_border=True, has_addons=True,
        )
        self.v25 = ProductVariant.objects.create(product=self.pizza, size=self.size_25, price=Decimal("13.50"))
        self.v32 = ProductVariant.objects.create(product=self.pizza, size=self.size_32, price=Decimal("26.50"))

        cheddar = PizzaBoard.objects.create(name="Чеддер")
        sausage = PizzaBoard.objects.create(name="Колбаски")
        self.board_25 = BoardParams.objects.create(board=cheddar, size=self.size_25, price=Decimal("2.50"))
        self.board_32 = BoardParams.objects.create(board=cheddar, size=self.size_32, price=Decimal("4.70"))
        self.board2_32 = BoardParams.objects.create(board=sausage, size=self.size_32, price=Decimal("3.00"))
        ham = PizzaAddon.objects.create(name="Ветчина")
        self.addon_25 = AddonParams.objects.create(addon=ham, size=self.size_25, price=Decimal("0.70"))
        self.addon_32 = AddonParams.objects.create(addon=ham, size=self.size_32, price=Decimal("0.90"))
        self.sauce = PizzaSauce.objects.create(name="Итальянский")

        self.combo = Product.objects.create(
            name="Комбо ОХОТА", slug="kombo", category=combo_cat, is_combo=True, has_drink=True
        )
        self.combo_variant = ProductVariant.objects.create(product=self.combo, value="1", unit="pcs", price=Decimal("33.00"))
        self.cola = ComboDrinks.objects.create(name="Coca Cola 1л.")

        self.token = self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json").json()["token"]

    def call(self, method, url, data=None, token=None):
        return getattr(self.client, method)(
            url, data, format="json", HTTP_X_CART_TOKEN=self.token if token is None else token
        )

    def pizza_32(self, **extra):
        return {"product_id": self.pizza.pk, "variant_id": self.v32.pk, "sauce_id": self.sauce.pk, **extra}

    def test_new_cart_is_empty(self):
        data = self.call("get", "/api/v1/cart/").json()
        self.assertEqual(data["branch_id"], self.branch.pk)
        self.assertEqual((data["items"], data["items_count"], data["subtotal"]), ([], 0, "0.00"))

    def test_unknown_or_missing_token_is_404(self):
        self.assertEqual(self.call("get", "/api/v1/cart/", token="").status_code, 404)
        self.assertEqual(self.call("get", "/api/v1/cart/", token=str(uuid.uuid4())).status_code, 404)

    def test_create_cart_needs_active_branch(self):
        response = self.client.post("/api/v1/cart/", {"branch_id": 999}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_price_is_variant_plus_boards_plus_addons_from_catalog(self):
        response = self.call("post", "/api/v1/cart/items/", self.pizza_32(
            board1_id=self.board_32.pk, board2_id=self.board2_32.pk, addon_ids=[self.addon_32.pk], quantity=2,
            price="0.01",  # цену от клиента сервер не читает
        ))
        self.assertEqual(response.status_code, 200, response.json())
        line = response.json()["items"][0]
        self.assertEqual(line["unit_price"], "35.10")  # 26.50 + 4.70 + 3.00 + 0.90
        self.assertEqual(line["total"], "70.20")
        self.assertEqual(response.json()["subtotal"], "70.20")
        self.assertEqual(line["sauce"]["id"], self.sauce.pk)

    def test_board_or_addon_of_other_size_is_rejected(self):
        board = self.call("post", "/api/v1/cart/items/", self.pizza_32(board1_id=self.board_25.pk))
        self.assertEqual(board.status_code, 400)
        self.assertIn("board1_id", board.json())
        addon = self.call("post", "/api/v1/cart/items/", self.pizza_32(addon_ids=[self.addon_25.pk]))
        self.assertEqual(addon.status_code, 400)
        self.assertIn("addon_ids", addon.json())

    def test_same_board_twice_is_rejected(self):
        response = self.call(
            "post", "/api/v1/cart/items/", self.pizza_32(board1_id=self.board_32.pk, board2_id=self.board_32.pk)
        )
        self.assertEqual(response.status_code, 400)

    def test_product_must_be_available_in_cart_branch(self):
        self.call("put", "/api/v1/cart/branch/", {"branch_id": self.other_branch.pk})
        response = self.call("post", "/api/v1/cart/items/", self.pizza_32())
        self.assertEqual(response.status_code, 400)
        self.assertIn("product_id", response.json())

    def test_sauce_required_for_pizza_and_drink_for_combo(self):
        no_sauce = self.call("post", "/api/v1/cart/items/", {"product_id": self.pizza.pk, "variant_id": self.v32.pk})
        self.assertIn("sauce_id", no_sauce.json())
        combo = {"product_id": self.combo.pk, "variant_id": self.combo_variant.pk}
        self.assertIn("drink_id", self.call("post", "/api/v1/cart/items/", combo).json())
        response = self.call("post", "/api/v1/cart/items/", {**combo, "drink_id": self.cola.pk})
        self.assertEqual(response.json()["items"][0]["drink"], "Coca Cola 1л.")

    def test_same_options_merge_and_quantity_is_capped(self):
        self.call("post", "/api/v1/cart/items/", self.pizza_32(addon_ids=[self.addon_32.pk], quantity=6))
        data = self.call("post", "/api/v1/cart/items/", self.pizza_32(addon_ids=[self.addon_32.pk], quantity=6)).json()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["quantity"], 10)
        data = self.call("post", "/api/v1/cart/items/", self.pizza_32()).json()
        self.assertEqual(len(data["items"]), 2)  # без добавки — отдельная строка

    def test_change_quantity_and_remove(self):
        item_id = self.call("post", "/api/v1/cart/items/", self.pizza_32()).json()["items"][0]["id"]
        data = self.call("patch", f"/api/v1/cart/items/{item_id}/", {"quantity": 3}).json()
        self.assertEqual(data["items_count"], 3)
        self.assertEqual(self.call("patch", f"/api/v1/cart/items/{item_id}/", {"quantity": 0}).status_code, 400)
        self.assertEqual(self.call("delete", f"/api/v1/cart/items/{item_id}/").json()["items"], [])

    def test_cannot_touch_item_of_another_cart(self):
        item_id = self.call("post", "/api/v1/cart/items/", self.pizza_32()).json()["items"][0]["id"]
        stranger = self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json").json()["token"]
        self.assertEqual(self.call("delete", f"/api/v1/cart/items/{item_id}/", token=stranger).status_code, 404)
        self.assertEqual(len(self.call("get", "/api/v1/cart/").json()["items"]), 1)

    def test_branch_change_clears_cart(self):
        self.call("post", "/api/v1/cart/items/", self.pizza_32())
        data = self.call("put", "/api/v1/cart/branch/", {"branch_id": self.other_branch.pk}).json()
        self.assertEqual((data["branch_id"], data["items"]), (self.other_branch.pk, []))
