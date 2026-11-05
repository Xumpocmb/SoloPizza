from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app_catalog.models import Category, Product, ProductVariant
from app_home.models import CafeBranch


class ProductBranchAvailabilityTests(TestCase):
    """Категория без привязки к филиалам прячет свои товары везде — как is_active=False."""

    def setUp(self):
        self.branch_a = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1", check_digit=1)
        self.branch_b = CafeBranch.objects.create(name="Северный", address="ул. Советская, 2", check_digit=2)
        self.linked_category = Category.objects.create(name="Пицца", slug="pizza")
        self.linked_category.branch.add(self.branch_a)
        self.orphan_category = Category.objects.create(name="Роллы", slug="rolls")
        self.product = Product.objects.create(name="Пепперони", slug="pepperoni", category=self.linked_category)
        self.orphan_product = Product.objects.create(name="Филадельфия", slug="philadelphia", category=self.orphan_category)

    def test_product_available_in_linked_branch(self):
        self.assertTrue(self.product.is_available_in_branch(self.branch_a))

    def test_product_unavailable_in_other_branch(self):
        self.assertFalse(self.product.is_available_in_branch(self.branch_b))

    def test_product_of_category_without_branches_is_unavailable_everywhere(self):
        self.assertFalse(self.orphan_product.is_available_in_branch(self.branch_a))
        self.assertFalse(self.orphan_product.is_available_in_branch(self.branch_b))
        self.assertFalse(self.orphan_product.is_available_in_branch(None))

    def test_check_without_branch_passes_linked_categories(self):
        self.assertTrue(self.product.is_available_in_branch(None))


class CatalogCurrencySignTests(TestCase):
    """Знак белорусского рубля выводится после цены, а не перед ней."""

    def setUp(self):
        self.category = Category.objects.create(name="Пицца", slug="pizza")
        self.product = Product.objects.create(
            name="Маргарита",
            slug="margarita",
            category=self.category,
        )
        ProductVariant.objects.create(product=self.product, value="1", price=Decimal("12.50"))

    def test_item_detail_puts_currency_sign_after_price(self):
        response = self.client.get(reverse("app_catalog:item_detail", args=[self.product.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '12,50 <span class="nbrb-icon">BYN</span>')
        self.assertNotContains(response, '<span class="nbrb-icon">BYN</span> 12,50')

    def test_staff_category_page_uses_currency_sign_instead_of_text(self):
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("app_catalog:category_detail", args=[self.category.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_catalog/category_detail_admin.html")
        self.assertContains(response, '12,50 <span class="nbrb-icon">BYN</span>')
        self.assertNotContains(response, "руб.")
