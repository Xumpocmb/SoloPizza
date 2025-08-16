from app_cart.models import CartItem
from app_home.models import CafeBranch, Discount
from app_catalog.models import Category
from django.conf import settings

DEFAULT_BRANCH_ID = 1


def site_context_processor(request):
    # Получаем филиалы из базы данных
    branches = CafeBranch.objects.filter(is_active=True)

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
    if request.user.is_authenticated:
        cart_total_quantity = CartItem.objects.total_quantity(request.user)
    else:
        cart_total_quantity = 0

    return {
        "cart_total_quantity": cart_total_quantity,
    }
