from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from app_catalog.models import Category, Product
from app_home.models import Vacancy
from app_reviews.models import Review
from django.conf import settings


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["app_home:home", "app_home:contacts", "app_home:delivery", "app_home:feedback", "app_home:vacancy_list", "app_catalog:catalog", "app_reviews:review_list"]

    def location(self, item):
        return reverse(item)

    def get_domain(self, site):
        # Используем домен из настроек
        return settings.DOMAIN_NAME.replace("http://", "").replace("https://", "")


class CategorySitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(is_active=True).exclude(slug="napitki-v-zal")

    def location(self, obj):
        return obj.get_absolute_url()

    def get_domain(self, site):
        # Используем домен из настроек
        return settings.DOMAIN_NAME.replace("http://", "").replace("https://", "")

    @property
    def protocol(self):
        # Определяем протокол из настроек домена
        if settings.DOMAIN_NAME.startswith("https://"):
            return "https"
        return "http"


class ProductSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()


def get_domain(self, site):
    # Используем домен из настроек
    return settings.DOMAIN_NAME.replace("http://", "").replace("https://", "")


@property
def protocol(self):
    # Определяем протокол из настроек домена
    if settings.DOMAIN_NAME.startswith("https://"):
        return "https"
    return "http"


class VacancySitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return Vacancy.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("app_home:vacancy_detail", kwargs={"vacancy_id": obj.id})


def get_domain(self, site):
    # Используем домен из настроек
    return settings.DOMAIN_NAME.replace("http://", "").replace("https://", "")


@property
def protocol(self):
    # Определяем протокол из настроек домена
    if settings.DOMAIN_NAME.startswith("https://"):
        return "https"
    return "http"


class ReviewSitemap(Sitemap):
    priority = 0.4
    changefreq = "weekly"

    def items(self):
        return Review.objects.filter(status="approved")

    def location(self, obj):
        return reverse("app_reviews:review_detail", kwargs={"pk": obj.pk})


def get_domain(self, site):
    # Используем домен из настроек
    return settings.DOMAIN_NAME.replace("http://", "").replace("https://", "")


@property
def protocol(self):
    # Определяем протокол из настроек домена
    if settings.DOMAIN_NAME.startswith("https://"):
        return "https"
    return "http"


@property
def protocol(self):
    # Определяем протокол из настроек домена
    if settings.DOMAIN_NAME.startswith("https://"):
        return "https"
    return "http"
