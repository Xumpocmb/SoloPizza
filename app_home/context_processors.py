from app_cart.models import CartItem
from app_home.models import CafeBranch, Discount, SnowSettings
from app_catalog.models import Category
from django.conf import settings
from app_cart.session_cart import SessionCart  # Import SessionCart

DEFAULT_BRANCH_ID = 1


def get_active_branches(request):
    """Активные филиалы вместе с телефонами и графиком, один запрос на запрос.

    Список живёт на request, поэтому контекстный процессор и представления берут
    одни и те же объекты: филиалы не выбираются заново в каждом шаблоне, а телефоны
    и график приходят вместе с ними.
    """
    branches = getattr(request, "_active_branches", None)
    if branches is None:
        branches = list(CafeBranch.objects.filter(is_active=True).prefetch_related("working_hours", "branch_phones"))
        request._active_branches = branches
    return branches


def site_context_processor(request):
    # Телефоны и график нужны шапке, подвалу, главной и микроразметке, поэтому
    # забираем их одним запросом и делимся одними и теми же объектами: иначе
    # branch_phones выбирается заново в каждом шаблоне, а branches — ещё раз
    # в restaurant_schema.
    branches = get_active_branches(request)

    # Initialize selected_branch_id with default value
    selected_branch_id = request.session.get("selected_branch_id", DEFAULT_BRANCH_ID)
    try:
        selected_branch_id = int(selected_branch_id)
    except (ValueError, TypeError):
        selected_branch_id = DEFAULT_BRANCH_ID

    selected_branch = next((branch for branch in branches if branch.id == selected_branch_id), None) or (branches[0] if branches else None)

    if not selected_branch:
        return {
            "branches": [],
            "categories": [],
            "selected_branch_id": None,
            "selected_branch": None,
        }

    if str(selected_branch_id) != str(selected_branch.id):
        request.session["selected_branch_id"] = str(selected_branch.id)

    # Получаем категории для конкретного филиала
    try:
        if request.user.is_superuser or request.user.is_staff:
            categories = Category.objects.filter(is_active=True, branch=selected_branch).order_by("order")
        else:
            categories = Category.objects.filter(is_active=True, branch=selected_branch, is_for_admin=False).order_by("order")
    except Exception:
        categories = []

    return {
        "branches": branches,
        "categories": categories,
        "selected_branch_id": str(selected_branch.id),
        "selected_branch": selected_branch,
    }


def cart_context(request):
    session_cart = SessionCart(request)
    cart_total_quantity = len(session_cart)  # SessionCart has __len__ method

    return {
        "cart_total_quantity": cart_total_quantity,
    }


def snow_context_processor(request):
    snow_settings, created = SnowSettings.objects.get_or_create(pk=1)
    return {
        "SNOW_ENABLED": snow_settings.is_enabled,
    }
