from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from app_catalog.models import Category, Product
from app_home.models import Vacancy


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        return [
            "app_home:home",
            "app_home:info",
            "app_home:contacts",
            "app_home:vacancy_list",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Category.objects.all().exclude(slug="napitki-v-zal")

    def location(self, obj):
        return reverse("app_catalog:category_detail", args=[obj.slug])


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Product.objects.filter(is_active=True).exclude(category__slug="napitki-v-zal")

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse("app_catalog:item_detail", args=[obj.slug])


class VacancySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Vacancy.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("app_home:vacancy_detail", kwargs={"vacancy_id": obj.id})
