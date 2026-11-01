from decimal import Decimal

from django.test import TestCase

from rest_framework.test import APIClient

from app_catalog.models import (
    AddonParams,
    BoardParams,
    Category,
    ComboDrinks,
    PizzaAddon,
    PizzaBoard,
    PizzaSizes,
    PizzaSauce,
    Product,
    ProductVariant,
)
from app_home.models import CafeBranch, CafeBranchPhone


class CatalogApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.branch_a = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", is_active=True)
        self.branch_b = CafeBranch.objects.create(name="Северный", address="ул. Советская, 2", is_active=True)
        CafeBranch.objects.create(name="Закрытый", address="ул. Мира, 3", is_active=False)
        CafeBranchPhone.objects.create(branch=self.branch_a, phone="+375 (29) 123-45-67")

        self.pizza = Category.objects.create(name="Пицца", slug="pizza")
        self.pizza.branch.add(self.branch_a)
        self.rolls = Category.objects.create(name="Роллы", slug="rolls")  # без филиалов — скрыта везде
        self.admin_cat = Category.objects.create(name="Для админа", slug="admin", is_for_admin=True)
        self.admin_cat.branch.add(self.branch_a)

        self.pepperoni = Product.objects.create(name="Пепперони", slug="pepperoni", category=self.pizza)
        Product.objects.create(name="Вискари", slug="whiskey", category=self.pizza, is_alcoholic=True)
        Product.objects.create(name="Филадельфия", slug="philadelphia", category=self.rolls)
        Product.objects.create(name="Скрытый", slug="hidden-pizza", category=self.admin_cat)

        self.size_25 = PizzaSizes.objects.create(name="25")
        self.size_32 = PizzaSizes.objects.create(name="32")
        ProductVariant.objects.create(product=self.pepperoni, size=self.size_32, price=Decimal("45.00"))
        ProductVariant.objects.create(product=self.pepperoni, size=self.size_25, price=Decimal("30.00"))

    def categories_url(self):
        return "/api/v1/categories/"

    def test_categories_only_for_branch(self):
        response = self.client.get(f"{self.categories_url()}?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 200)
        slugs = [c["slug"] for c in response.json()]
        self.assertEqual(slugs, ["pizza"])

    def test_category_without_branch_is_invisible(self):
        response = self.client.get(f"{self.categories_url()}?branch_id={self.branch_b.pk}")
        self.assertEqual(response.json(), [])

    def test_branch_id_required(self):
        self.assertEqual(self.client.get(self.categories_url()).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/products/").status_code, 400)

    def test_unknown_or_inactive_branch_is_404(self):
        self.assertEqual(self.client.get(f"{self.categories_url()}?branch_id=9999").status_code, 404)
        inactive = CafeBranch.objects.get(name="Закрытый")
        self.assertEqual(self.client.get(f"{self.categories_url()}?branch_id={inactive.pk}").status_code, 404)

    def test_category_detail_hides_alcoholic_and_counts_visible_products(self):
        response = self.client.get(f"/api/v1/categories/pizza/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["product_count"], 1)
        self.assertEqual([p["slug"] for p in data["products"]], ["pepperoni"])

    def test_admin_category_detail_is_404(self):
        response = self.client.get(f"/api/v1/categories/admin/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 404)

    def test_products_filtered_by_category(self):
        response = self.client.get(f"/api/v1/products/?branch_id={self.branch_a.pk}&category=pizza")
        slugs = [p["slug"] for p in response.json()]
        self.assertEqual(slugs, ["pepperoni"])

    def test_product_detail_min_price_and_variants(self):
        response = self.client.get(f"/api/v1/products/pepperoni/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(Decimal(str(data["min_price"])), Decimal("30.00"))
        self.assertEqual([v["size"] for v in data["variants"]], ["25", "32"])

    def test_alcoholic_product_is_404(self):
        response = self.client.get(f"/api/v1/products/whiskey/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 404)

    def test_product_of_orphan_category_is_404(self):
        response = self.client.get(f"/api/v1/products/philadelphia/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 404)

    def test_product_detail_options_follow_product_flags(self):
        sauce = PizzaSauce.objects.create(name="Сырный", slug="cheese-sauce", is_active=True)
        board = PizzaBoard.objects.create(name="Сырный борт", slug="cheese-board", is_active=True)
        addon = PizzaAddon.objects.create(name="Оливки", slug="olives", is_active=True)
        BoardParams.objects.create(board=board, size=self.size_32, price=Decimal("10.00"))
        AddonParams.objects.create(addon=addon, size=self.size_32, price=Decimal("3.00"))
        pizza = Product.objects.create(
            name="Маргарита",
            slug="margherita",
            category=self.pizza,
            has_base_sauce=True,
            has_border=True,
            has_addons=True,
            has_drink=True,
        )
        variant = ProductVariant.objects.create(product=pizza, size=self.size_32, price=Decimal("40.00"))

        response = self.client.get(f"/api/v1/products/margherita/?branch_id={self.branch_a.pk}")
        data = response.json()
        self.assertEqual([s["id"] for s in data["sauces"]], [sauce.pk])
        self.assertEqual(len(data["variants"][0]["boards"]), 1)
        self.assertEqual(len(data["variants"][0]["addons"]), 1)
        self.assertTrue(data["has_drink"])
        self.assertEqual(len(data["drinks"]), 0)  # ComboDrinks пустые

    def test_combo_uses_size_32_boards(self):
        combo_size = PizzaSizes.objects.create(name="28")
        board = PizzaBoard.objects.create(name="Сырный борт", slug="cheese-board-combo", is_active=True)
        board_32 = BoardParams.objects.create(board=board, size=self.size_32, price=Decimal("10.00"))
        combo = Product.objects.create(name="Комбо", slug="combo", category=self.pizza, is_combo=True, has_border=True)
        variant = ProductVariant.objects.create(product=combo, size=combo_size, price=Decimal("60.00"))

        response = self.client.get(f"/api/v1/products/combo/?branch_id={self.branch_a.pk}")
        data = response.json()
        boards = data["variants"][0]["boards"]
        self.assertEqual([b["id"] for b in boards], [board_32.pk])

    def test_branches_list_active_only_with_phones(self):
        response = self.client.get("/api/v1/branches/")
        self.assertEqual(response.status_code, 200)
        names = [b["name"] for b in response.json()]
        self.assertEqual(sorted(names), ["Северный", "Центральный"])
        central = next(b for b in response.json() if b["name"] == "Центральный")
        self.assertEqual(central["phones"], ["+375291234567"])

    def test_meta(self):
        response = self.client.get("/api/v1/meta/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["currency"], "BYN")
        self.assertEqual(data["timezone"], "Europe/Minsk")
