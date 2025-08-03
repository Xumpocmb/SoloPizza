from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from app_cart.models import CartItem
from app_cart.utils import validate_cart_items_for_branch
from app_catalog.models import Product
from app_home.models import CafeBranch


def home_page(request):
    return render(request, "app_home/home.html")


@require_POST
def select_branch(request):
    branch_id = request.POST.get("branch_id")
    try:
        if branch_id:
            branch = CafeBranch.objects.get(id=branch_id)
            request.session["selected_branch_id"] = branch_id
            messages.success(request, "Филиал изменен!", extra_tags="success")

            cart_items = CartItem.objects.filter(user=request.user).select_related('item__category')
            unavailable_items = validate_cart_items_for_branch(cart_items, branch)

            if unavailable_items:
                messages.warning(
                    request,
                    f"Некоторые товары в корзине недоступны в филиале '{branch.name}'. "
                    "Пожалуйста, удалите их перед оформлением заказа."
                )

            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "Ошибка: филиал не выбран!", extra_tags="error")
    except CafeBranch.DoesNotExist:
        messages.error(request, "Выбранный филиал не найден", extra_tags="error")
        return redirect('/')
    return redirect(request.META.get("HTTP_REFERER"))


def discounts_view(request):
    pizza_weekly = Product.objects.filter(category__slug="picca", is_active=True, is_weekly_special=True).first()
    context = {"pizza_weekly": pizza_weekly}
    return render(request, "app_home/discounts.html", context=context)
