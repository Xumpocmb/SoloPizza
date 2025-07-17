from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from app_catalog.models import Product


def home_page(request):
    return render(request, "app_home/home.html")


@require_POST
def select_branch(request):
    branch_id = request.POST.get("branch_id")
    print(branch_id)
    if branch_id:
        request.session["selected_branch_id"] = branch_id
        messages.success(request, "Филиал изменен!", extra_tags="success")
    else:
        messages.error(request, "Ошибка: филиал не выбран!", extra_tags="error")
    return redirect(request.META.get("HTTP_REFERER"))


def discounts_view(request):
    pizza_weekly = Product.objects.filter(category__slug="picca", is_active=True, is_weekly_special=True).first()
    context = {"pizza_weekly": pizza_weekly}
    return render(request, "app_home/discounts.html", context=context)
