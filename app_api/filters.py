from django.db.models import Count, Min, Q

from app_catalog.models import Category, Product
from app_home.models import CafeBranch

# Правила видимости каталога совпадают с web-меню (app_home/context_processors.py)
# и с MVP мобильного приложения: алкоголь скрыт, категории «для админа» скрыты,
# категория без привязки к филиалу недоступна нигде.


def branch_or_none(raw_branch_id):
    """Филиал по id из query-параметра; None, если id нет или он не число."""
    if raw_branch_id is None or not str(raw_branch_id).isdigit():
        return None
    return CafeBranch.objects.filter(pk=raw_branch_id, is_active=True).first()


def visible_categories(branch_id):
    return Category.objects.filter(
        is_active=True,
        is_for_admin=False,
        branch=branch_id,
    ).order_by("order", "id").annotate(
        product_count=Count("products", filter=Q(products__is_active=True, products__is_alcoholic=False), distinct=True)
    )


def catalog_products(branch_id, category=None):
    products = Product.objects.filter(
        is_active=True,
        is_alcoholic=False,
        category__is_active=True,
        category__is_for_admin=False,
        category__branch=branch_id,
    ).annotate(min_price=Min("variants__price")).select_related("category").prefetch_related("variants__size")
    if category is not None:
        products = products.filter(category=category)
    return products
