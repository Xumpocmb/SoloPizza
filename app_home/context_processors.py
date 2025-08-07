from app_cart.models import CartItem
from app_home.models import CafeBranch
from app_catalog.models import Category
from django.core.cache import cache
from django.conf import settings

DEFAULT_BRANCH_ID = 1

# Константы для ключей кеша
CACHE_KEY_BRANCHES = 'cafe_branches_active'
CACHE_TIMEOUT = 60 * 60 * 24  # 24 часа


def site_context_processor(request):
    # Получаем филиалы из кеша или из базы данных
    branches = cache.get(CACHE_KEY_BRANCHES)
    if branches is None:
        branches = CafeBranch.objects.filter(is_active=True)
        # Сохраняем в кеш
        cache.set(CACHE_KEY_BRANCHES, branches, CACHE_TIMEOUT)

    # Initialize selected_branch_id with default value
    selected_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)
    try:
        selected_branch_id = int(selected_branch_id)
    except (ValueError, TypeError):
        selected_branch_id = DEFAULT_BRANCH_ID

    try:
        selected_branch = branches.get(id=selected_branch_id)
    except CafeBranch.DoesNotExist:
        selected_branch = branches.first()

    if not selected_branch:
        return {
            "branches": [],
            "categories": [],
            "selected_branch_id": None,
            "selected_branch": None,
        }

    if str(selected_branch_id) != str(selected_branch.id):
        request.session["selected_branch_id"] = str(selected_branch.id)

    # Ключ кеша для категорий конкретного филиала
    cache_key_categories = f'categories_branch_{selected_branch.id}_admin_{request.user.is_superuser}'
    
    # Пробуем получить категории из кеша
    categories = cache.get(cache_key_categories)
    
    if categories is None:
        try:
            if request.user.is_superuser:
                categories = Category.objects.filter(is_active=True, branch=selected_branch).order_by("order")
            else:
                categories = Category.objects.filter(is_active=True, branch=selected_branch, is_for_admin=False).order_by("order")
            # Сохраняем в кеш
            cache.set(cache_key_categories, categories, CACHE_TIMEOUT)
        except Exception:
            categories = []

    return {
        "branches": branches,
        "categories": categories,
        "selected_branch_id": str(selected_branch.id),
        "selected_branch": selected_branch,
    }


def cart_context(request):
    if request.user.is_authenticated:
        cart_total_quantity = CartItem.objects.total_quantity(request.user)
    else:
        cart_total_quantity = 0

    return {
        "cart_total_quantity": cart_total_quantity,
    }
