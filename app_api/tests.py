from decimal import Decimal
from unittest import mock

from django.conf import settings
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
    PizzaSizes,
    PizzaSauce,
    Product,
    ProductVariant,
)
from app_home.models import CafeBranch, CafeBranchPhone, Vacancy, VacancyApplication


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

    def test_featured_products_only_display_on_main(self):
        Product.objects.filter(pk=self.pepperoni.pk).update(display_on_main=True)
        response = self.client.get(f"/api/v1/products/featured/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["slug"] for p in response.json()], ["pepperoni"])
        self.assertEqual(Decimal(str(response.json()[0]["min_price"])), Decimal("30.00"))

    def test_featured_respects_branch_and_visibility(self):
        Product.objects.update(display_on_main=True)

        response = self.client.get(f"/api/v1/products/featured/?branch_id={self.branch_a.pk}")
        self.assertEqual([p["slug"] for p in response.json()], ["pepperoni"])

        self.assertEqual(self.client.get(f"/api/v1/products/featured/?branch_id={self.branch_b.pk}").json(), [])
        self.assertEqual(self.client.get("/api/v1/products/featured/").status_code, 400)

    def test_weekly_special_returns_single_product(self):
        Product.objects.filter(pk=self.pepperoni.pk).update(is_weekly_special=True)
        response = self.client.get(f"/api/v1/products/weekly-special/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["slug"], "pepperoni")
        self.assertTrue(data["is_weekly_special"])
        self.assertEqual([v["size"] for v in data["variants"]], ["25", "32"])

    def test_weekly_special_absent_or_invisible_is_404(self):
        response = self.client.get(f"/api/v1/products/weekly-special/?branch_id={self.branch_a.pk}")
        self.assertEqual(response.status_code, 404)

        Product.objects.filter(pk=self.pepperoni.pk).update(is_weekly_special=True)
        self.assertEqual(self.client.get(f"/api/v1/products/weekly-special/?branch_id={self.branch_b.pk}").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/products/weekly-special/").status_code, 400)

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


# DEBUG=False включает отправку уведомления об отклике, а троттлинг пишет историю
# в кэш — в проде это Redis, в тестах локальный memory backend.
@override_settings(
    DEBUG=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class VacancyApiTests(TestCase):
    payload = {
        "name": "Иван Иванов",
        "age": 24,
        "phone": "+375 (29) 123-45-67",
        "experience_years": 3,
        "work_experience": "Три года службы доставки",
    }

    def setUp(self):
        self.client = APIClient()
        cache.clear()  # locmem живёт весь прогон, счётчик троттлинга нужен с нуля
        self.courier = Vacancy.objects.create(
            title="Курьер",
            description="Доставка заказов",
            salary="от 1200 руб",
            benefits="Гибкий график, компенсация связи",
            is_active=True,
        )
        self.closed = Vacancy.objects.create(title="Повар", description="Горячий цех", is_active=False)

    def test_vacancies_active_only(self):
        response = self.client.get("/api/v1/vacancies/")
        self.assertEqual(response.status_code, 200)
        titles = [v["title"] for v in response.json()]
        self.assertEqual(titles, ["Курьер"])

    def test_vacancy_detail_splits_benefits(self):
        response = self.client.get(f"/api/v1/vacancies/{self.courier.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["description"], "Доставка заказов")
        self.assertEqual(data["benefits"], ["Гибкий график", "компенсация связи"])

    def test_inactive_vacancy_is_404(self):
        self.assertEqual(self.client.get(f"/api/v1/vacancies/{self.closed.pk}/").status_code, 404)
        self.assertEqual(
            self.client.post(f"/api/v1/vacancies/{self.closed.pk}/applications/", self.payload, format="json").status_code,
            404,
        )

    @override_settings(DEBUG=False)
    def test_application_is_created_with_cleaned_phone(self):
        # Как и web-вьюха, уведомление в Telegram уходит только вне DEBUG.
        with mock.patch("app_home.tasks.send_vacancy_application_notification") as notify:
            response = self.client.post(f"/api/v1/vacancies/{self.courier.pk}/applications/", self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.json())

        application = VacancyApplication.objects.get()
        self.assertEqual(application.vacancy, self.courier)
        self.assertEqual(application.phone, "375291234567")
        self.assertEqual(response.json()["phone"], "375291234567")
        notify.delay.assert_called_once_with(application.pk)

    def test_application_validation(self):
        url = f"/api/v1/vacancies/{self.courier.pk}/applications/"
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)

        too_short = {**self.payload, "phone": "+375 29 123"}
        self.assertIn("phone", self.client.post(url, too_short, format="json").json())
        too_long = {**self.payload, "phone": "8" * 18}
        self.assertIn("phone", self.client.post(url, too_long, format="json").json())

        for age in (15, 101):
            self.assertIn("age", self.client.post(url, {**self.payload, "age": age}, format="json").json())
        self.assertIn(
            "experience_years",
            self.client.post(url, {**self.payload, "experience_years": 51}, format="json").json(),
        )
        self.assertEqual(VacancyApplication.objects.count(), 0)

    def test_application_is_throttled_per_ip(self):
        url = f"/api/v1/vacancies/{self.courier.pk}/applications/"
        limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"].split("/")[0])

        with mock.patch("app_home.tasks.send_vacancy_application_notification"):
            for _ in range(limit):
                self.assertEqual(self.client.post(url, self.payload, format="json").status_code, 201)
            self.assertEqual(self.client.post(url, self.payload, format="json").status_code, 429)
